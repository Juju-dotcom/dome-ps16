#include <Arduino.h>
#include <Wire.h>
#include <AccelStepper.h>
#include <Adafruit_NeoPixel.h>
#include <U8g2lib.h>

#define FW_VERSION "1.2"

const uint8_t PIN_STEP      = 2;
const uint8_t PIN_DIR       = 3;
const uint8_t PIN_EN        = 4;
const uint8_t PIN_TRIG      = 5;
const uint8_t PIN_WS        = 6;
const uint8_t PIN_BTN_START = 7;
const uint8_t PIN_BTN_NEXT  = 8;
const uint8_t PIN_BTN_STOP  = 9;
const uint8_t PIN_OLED_RST  = 10;
const uint8_t PIN_HOME      = 18;

const uint8_t NB_LED        = 16;

static inline uint8_t ledPin(uint8_t k) { return 21 + k; }

const long  STEPS_PER_REV = 3200;
const float ROT_VMAX      = 800.0;
const float ROT_ACCEL     = 400.0;
const bool  DIR_INVERSE   = false;

const int     HOME_DIR          = -1;
const uint8_t HOME_ACTIVE_LEVEL = HIGH;

const float   HOME_SPEED        = 400.0;
const float   HOME_ACCEL        = 400.0;
const long    HOME_MAX_STEPS    = 4000;
const long    HOME_BACKOFF_STEPS = 480;
const uint8_t SENSOR_FILTER_MS  = 3;
const uint16_t MOTOR_WAKE_MS    = 10;
const uint32_t MOTOR_IDLE_OFF_MS = 120000UL;

const uint32_t LED_MAX_ON_MS   = 10000UL;
const uint16_t TRIG_PULSE_MS   = 10;
const uint16_t SEQ_ATTENTE_DEFAUT_MS = 50;
const uint16_t SEQ_ATTENTE_MAX_MS    = 2000;
const uint16_t SEQ_MARGE_MS    = 50;
const uint16_t SEQ_RESERVE_MS  = 1000;

const uint16_t SEQ_PERIODE_MIN_MS = 150;
const uint16_t BTN_POSE_MS     = 500;

const uint8_t  DEBOUNCE_MS     = 30;
const uint32_t TEST_DUREE_MS   = 30000UL;
const uint16_t TEST_OLED_PHASE_MS = 2000;
const uint16_t TEST_WS_PHASE_MS   = 1000;

const uint8_t WS_LUMINOSITE    = 40;

#define WS_ORDRE NEO_GRB

const uint8_t  OLED_I2C_ADDR   = 0x3C;
const uint16_t OLED_MIN_MS     = 100;
#define OLED_ROTATION U8G2_R1
const uint8_t OLED_W = 128, OLED_H = 64;

AccelStepper stepper(AccelStepper::DRIVER, PIN_STEP, PIN_DIR);
Adafruit_NeoPixel strip(1, PIN_WS, WS_ORDRE + NEO_KHZ800);

U8G2_SH1107_64X128_F_HW_I2C u8g2(OLED_ROTATION, PIN_OLED_RST);

enum : uint8_t { ETAT_PRET, ETAT_OCCUPE, ETAT_ARRET, ETAT_ERREUR };
uint8_t latched = ETAT_PRET;

uint8_t  ledCur  = 0;
uint8_t  ledLast = 0;
uint32_t ledOnAt = 0;

bool     trigActive = false;
uint32_t trigT0 = 0;

enum : uint8_t { SEQ_OFF, SEQ_ATTENTE, SEQ_POSE, SEQ_PAUSE };
uint8_t  seqPhase = SEQ_OFF;
uint8_t  seqK = 0;
uint16_t seqPose = 0, seqAttente = 0;
uint32_t seqT0 = 0, seqT1 = 0, seqDebut = 0;
bool     seqDone = false;
uint32_t seqDurMs = 0;

enum : uint8_t { MC_NONE, MC_HOME, MC_ROT, MC_GOTO };
enum : uint8_t { PH_NONE, PH_MOVE, PH_CLEAR, PH_BACKOFF, PH_SEEK, PH_STOP, PH_RETURN };
uint8_t  mvCmd = MC_NONE, mvPhase = PH_NONE;
float    mvArg = 0;
long     homeEdge = 0;
bool     homed = false;
bool     motorOn = false;
uint32_t motorOnAt = 0, motorLastActive = 0;
uint32_t mvT0 = 0;

bool     sensRaw = false, sensStable = false;
uint32_t sensT = 0;

struct Btn { uint8_t pin; bool raw; bool stable; uint32_t t; uint16_t presses; uint16_t trans; };
Btn btn[3] = {
  { PIN_BTN_START, false, false, 0, 0, 0 },
  { PIN_BTN_NEXT,  false, false, 0, 0, 0 },
  { PIN_BTN_STOP,  false, false, 0, 0, 0 }
};
const char* const BTN_NOM[3] = { "DEMARRER", "SUIVANT", "ARRET" };

enum : uint8_t { T_NONE, T_BOUTONS, T_CAPTEUR, T_OLED, T_WS };
uint8_t  testMode = T_NONE;
uint8_t  testStep = 255;
uint32_t testT0 = 0;
uint16_t testCount = 0;
bool     testSens = false;

bool     wsOverrideOn = false;
uint32_t wsOverride = 0, wsLast = 0xFFFFFFFFUL;
bool     oledOk = false;
char     oledDrawn[4][24];
uint32_t oledLastMs = 0;
uint16_t oledDurMs  = 0;

char    rx[64];
uint8_t rxN = 0;
bool    rxOver = false;

static long roundL(float x) { return (long)(x >= 0 ? x + 0.5f : x - 0.5f); }
static long normSteps(long s) { s %= STEPS_PER_REV; if (s < 0) s += STEPS_PER_REV; return s; }
static long posMod() { return normSteps(stepper.currentPosition()); }
static float angleDeg() { return posMod() * (360.0f / (float)STEPS_PER_REV); }
static long angleTenths() { return posMod() * 3600L / STEPS_PER_REV; }

static bool parseLong(const char* s, long& v) {
  char* e; v = strtol(s, &e, 10); return (*s != 0 && *e == 0);
}
static bool parseFloat(const char* s, float& v) {
  char* e; v = (float)strtod(s, &e); return (*s != 0 && *e == 0);
}

static uint8_t deriveState() {
  if (latched != ETAT_PRET) return latched;
  if (seqPhase != SEQ_OFF || mvCmd != MC_NONE || testMode != T_NONE) return ETAT_OCCUPE;
  return ETAT_PRET;
}
static const __FlashStringHelper* etatAscii(uint8_t e) {
  switch (e) {
    case ETAT_OCCUPE: return F("OCCUPE");
    case ETAT_ARRET:  return F("ARRET");
    case ETAT_ERREUR: return F("ERREUR");
    default:          return F("PRET");
  }
}
static const __FlashStringHelper* mvName() {
  switch (mvCmd) {
    case MC_HOME: return F("HOME");
    case MC_ROT:  return F("ROT");
    default:      return F("GOTO");
  }
}
static const __FlashStringHelper* testName() {
  switch (testMode) {
    case T_BOUTONS: return F("BOUTONS");
    case T_CAPTEUR: return F("CAPTEUR");
    case T_OLED:    return F("OLED");
    default:        return F("WS");
  }
}
static void clearLatch() { latched = ETAT_PRET; seqDone = false; }

static void errLn(const __FlashStringHelper* cmd, const __FlashStringHelper* msg) {
  Serial.print(F("ERR ")); Serial.print(cmd); Serial.print(' '); Serial.println(msg);
}

static void ledAllOff() {
  for (uint8_t k = 1; k <= NB_LED; k++) digitalWrite(ledPin(k), LOW);
  ledCur = 0;
}

static void ledOn(uint8_t k) {
  if (k < 1 || k > NB_LED) return;
  if (ledCur == k) return;
  ledAllOff();
  digitalWrite(ledPin(k), HIGH);
  ledCur = k; ledLast = k; ledOnAt = millis();
}

static void motorEnable(bool on) {
  if (on) {
    if (!motorOn) { digitalWrite(PIN_EN, LOW); motorOn = true; motorOnAt = millis(); }
  } else {
    digitalWrite(PIN_EN, HIGH); motorOn = false;
  }
}
static bool motorReady() { return motorOn && (uint32_t)(millis() - motorOnAt) >= MOTOR_WAKE_MS; }

static void trigStart() { digitalWrite(PIN_TRIG, HIGH); trigActive = true; trigT0 = millis(); }
static void updateTrig() {
  if (trigActive && (uint32_t)(millis() - trigT0) >= TRIG_PULSE_MS) {
    digitalWrite(PIN_TRIG, LOW); trigActive = false;
  }
}

static uint32_t wsColorOfState(uint8_t e) {
  switch (e) {
    case ETAT_OCCUPE: return strip.Color(0, 0, 255);
    case ETAT_ARRET:
    case ETAT_ERREUR: return strip.Color(255, 0, 0);
    default:          return strip.Color(0, 255, 0);
  }
}
static void wsUpdate() {
  uint32_t c = wsOverrideOn ? wsOverride : wsColorOfState(deriveState());
  if (c != wsLast) { strip.setPixelColor(0, c); strip.show(); wsLast = c; }
}

static void oledInvalidate() { oledDrawn[0][0] = (char)0xFF; }

#define DEG "\xC2\xB0"
static void oledBuildLines(char L[4][24]) {
  memset(L, 0, 4 * 24);
  uint8_t e = deriveState();
  const char* t;
  if (e == ETAT_ARRET)               t = "STOPPED";
  else if (e == ETAT_ERREUR)         t = "ERROR";
  else if (seqPhase != SEQ_OFF)      t = "SCANNING";
  else if (mvCmd == MC_HOME)         t = "HOMING";
  else if (mvCmd != MC_NONE)         t = "ROTATING";
  else if (testMode != T_NONE)       t = "TEST";
  else if (seqDone)                  t = "DONE";
  else                               t = "READY";
  snprintf(L[0], 24, "%s", t);

  long a = angleTenths();
  if (testMode == T_BOUTONS) {
    snprintf(L[1], 24, "S:%c  N:%c  X:%c", btn[0].stable ? '#' : '.', btn[1].stable ? '#' : '.', btn[2].stable ? '#' : '.');
  } else if (testMode == T_CAPTEUR) {
    snprintf(L[1], 24, "Sensor: %s", sensStable ? "BLOCKED" : "CLEAR");
  } else if (ledCur) {
    snprintf(L[1], 24, "LED %02d/%d  %ld.%ld" DEG, (int)ledCur, (int)NB_LED, a / 10, a % 10);
  } else {
    snprintf(L[1], 24, "LED --/%d  %ld.%ld" DEG, (int)NB_LED, a / 10, a % 10);
  }

  char v[10];
  if (seqPhase != SEQ_OFF) {
    snprintf(L[2], 24, "Image %d of %d", (int)seqK, (int)NB_LED);
    L[3][0] = '\x01'; L[3][1] = (char)(seqK - 1);
  } else if (mvCmd == MC_HOME) {
    snprintf(L[2], 24, "Finding zero...");
    snprintf(L[3], 24, "Please wait");
  } else if (mvCmd != MC_NONE) {
    dtostrf(mvArg, 0, 1, v);
    snprintf(L[2], 24, mvCmd == MC_ROT ? "Turning %s" DEG : "Going to %s" DEG, v);
    snprintf(L[3], 24, "Please wait");
  } else if (testMode != T_NONE) {
    snprintf(L[2], 24, "Test running");
    snprintf(L[3], 24, "STOP to end");
  } else if (seqDone) {
    dtostrf(seqDurMs / 1000.0f, 0, 1, v);
    snprintf(L[2], 24, "%d images in %s s", (int)NB_LED, v);
    L[3][0] = '\x01'; L[3][1] = (char)NB_LED;
  } else if (e == ETAT_ARRET) {
    snprintf(L[2], 24, "Stopped by user");
    snprintf(L[3], 24, "START to scan again");
  } else if (e == ETAT_ERREUR) {
    snprintf(L[2], 24, "See serial log");
    snprintf(L[3], 24, "START to retry");
  } else {
    snprintf(L[2], 24, "Home: %s", homed ? "OK" : "not set");
    snprintf(L[3], 24, "START = scan");
  }
}

static void oledDrawBar(uint8_t done) {
  const uint8_t x = 0, y = 51, w = 96, h = 12;
  u8g2.drawRFrame(x, y, w, h, 3);
  uint8_t fill = (uint8_t)((uint16_t)(w - 4) * done / NB_LED);
  if (fill) u8g2.drawRBox(x + 2, y + 2, fill, h - 4, 1);
  char c[8]; snprintf(c, sizeof(c), "%d/%d", (int)done, (int)NB_LED);
  u8g2.drawUTF8(w + 4, y + 10, c);
}

static void oledDraw(char L[4][24]) {
  u8g2.clearBuffer();
  u8g2.drawRBox(0, 0, OLED_W, 17, 3);
  u8g2.setDrawColor(0);
  u8g2.setFont(u8g2_font_7x13B_tf);
  u8g2.drawUTF8(4, 13, L[0]);
  u8g2.setFont(u8g2_font_5x8_tf);
  u8g2.drawUTF8(OLED_W - 33, 11, "PS-16");
  u8g2.setDrawColor(1);
  u8g2.setFont(u8g2_font_6x12_tf);
  u8g2.drawUTF8(0, 31, L[1]);
  u8g2.drawUTF8(0, 45, L[2]);
  if (L[3][0] == '\x01') oledDrawBar((uint8_t)L[3][1]);
  else                   u8g2.drawUTF8(0, 61, L[3]);
  uint32_t t0 = millis();
  u8g2.sendBuffer();
  oledDurMs = (uint16_t)(millis() - t0);
}

static void oledRefresh(bool force) {
  if (!oledOk) return;
  char L[4][24];
  oledBuildLines(L);
  if (!force && memcmp(L, oledDrawn, sizeof(L)) == 0) return;
  oledDraw(L);
  memcpy(oledDrawn, L, sizeof(L));
  oledLastMs = millis();
}

static void oledSplash() {
  const uint8_t N = 12;
  for (uint8_t i = 0; i <= N; i++) {
    u8g2.clearBuffer();
    u8g2.setFont(u8g2_font_10x20_tf);
    u8g2.drawUTF8(14, 20, "DOME PS-16");
    u8g2.setFont(u8g2_font_6x12_tf);
    u8g2.drawUTF8(10, 36, "Photometric Stereo");
    u8g2.setFont(u8g2_font_5x8_tf);
    u8g2.drawUTF8(52, 63, "v" FW_VERSION);
    u8g2.drawRFrame(14, 46, 100, 10, 3);
    uint8_t fill = (uint8_t)(96u * i / N);
    if (fill) u8g2.drawRBox(16, 48, fill, 6, 1);
    u8g2.sendBuffer();
    strip.setPixelColor(0, strip.gamma32(strip.ColorHSV((uint16_t)(65535UL * i / N))));
    strip.show();
    delay(100);
  }
  strip.setPixelColor(0, 0); strip.show(); wsLast = 0xFFFFFFFFUL;
}

static bool oledAllowed() {
  return oledOk && testMode != T_OLED && mvCmd == MC_NONE && seqPhase == SEQ_OFF &&
         (uint32_t)(millis() - oledLastMs) >= OLED_MIN_MS;
}

static void oledTestPattern(uint8_t step) {
  const uint8_t w = OLED_W, h = OLED_H;
  u8g2.clearBuffer();
  if (step == 0) {
    u8g2.drawFrame(0, 0, w, h);
    u8g2.setFont(u8g2_font_6x12_tf);
    u8g2.drawUTF8(10, 13, "TOP   OLED TEST");
    char b[24]; snprintf(b, sizeof(b), "Lib: %dx%d", (int)u8g2.getDisplayWidth(), (int)u8g2.getDisplayHeight());
    u8g2.drawUTF8(10, 27, b);
    u8g2.drawUTF8(10, 41, "Ready Stop 90.0" DEG);
    u8g2.drawUTF8(10, 55, "0123456789 ABCxyz");
    u8g2.drawBox(0, 0, 5, 5); u8g2.drawBox(w - 5, 0, 5, 5);
    u8g2.drawBox(0, h - 5, 5, 5); u8g2.drawBox(w - 5, h - 5, 5, 5);
  } else if (step == 1) {
    for (uint8_t y = 0; y < h; y += 8)
      for (uint8_t x = 0; x < w; x += 8)
        if (((x / 8) + (y / 8)) % 2 == 0) u8g2.drawBox(x, y, 8, 8);
  } else {
    u8g2.drawBox(0, 0, w, h);
  }
  u8g2.sendBuffer();
}

static void testEnd(bool interrompu) {
  Serial.print(F("OK TEST ")); Serial.print(testName());
  switch (testMode) {
    case T_BOUTONS:
      Serial.print(F(" demarrer=")); Serial.print(btn[0].presses);
      Serial.print(F(" suivant="));  Serial.print(btn[1].presses);
      Serial.print(F(" arret="));    Serial.print(btn[2].presses);
      Serial.print(F(" transitions_brutes="));
      Serial.print(btn[0].trans); Serial.print('/'); Serial.print(btn[1].trans); Serial.print('/'); Serial.print(btn[2].trans);
      break;
    case T_CAPTEUR:
      Serial.print(F(" changements=")); Serial.print(testCount);
      break;
    default: break;
  }
  if (interrompu) Serial.print(F(" (interrompu)"));
  Serial.println();
  testMode = T_NONE; wsOverrideOn = false; oledInvalidate();
}

static void testStart(uint8_t mode) {
  clearLatch();
  testMode = mode; testStep = 255; testT0 = millis(); testCount = 0;
  if (mode == T_BOUTONS) {
    for (uint8_t i = 0; i < 3; i++) { btn[i].presses = 0; btn[i].trans = 0; }
    Serial.println(F("EVT TEST BOUTONS: appuie sur chaque bouton (30 s, OFF pour finir)"));
  } else if (mode == T_CAPTEUR) {
    testSens = sensStable;
    Serial.print(F("EVT CAPTEUR niveau=")); Serial.print(digitalRead(PIN_HOME));
    Serial.print(F(" etat=")); Serial.println(sensStable ? F("OCCULTE") : F("LIBRE"));
  }
}

static void updateTest() {
  if (testMode == T_NONE) return;
  uint32_t dt = (uint32_t)(millis() - testT0);
  switch (testMode) {
    case T_BOUTONS:
      if (dt >= TEST_DUREE_MS) testEnd(false);
      break;
    case T_CAPTEUR:
      if (sensStable != testSens) {
        testSens = sensStable; testCount++;
        Serial.print(F("EVT CAPTEUR niveau=")); Serial.print(digitalRead(PIN_HOME));
        Serial.print(F(" etat=")); Serial.println(sensStable ? F("OCCULTE") : F("LIBRE"));
      }
      wsOverrideOn = true;
      wsOverride = sensStable ? strip.Color(255, 0, 0) : strip.Color(0, 255, 0);
      if (dt >= TEST_DUREE_MS) testEnd(false);
      break;
    case T_OLED: {
      uint8_t s = dt / TEST_OLED_PHASE_MS;
      if (s != testStep) {
        testStep = s;
        if (s >= 3) testEnd(false); else oledTestPattern(s);
      }
      break;
    }
    case T_WS: {
      uint8_t s = dt / TEST_WS_PHASE_MS;
      if (s != testStep) {
        testStep = s;
        wsOverrideOn = true;
        switch (s) {
          case 0: wsOverride = strip.Color(255, 0, 0);     Serial.println(F("EVT WS ROUGE")); break;
          case 1: wsOverride = strip.Color(0, 255, 0);     Serial.println(F("EVT WS VERT"));  break;
          case 2: wsOverride = strip.Color(0, 0, 255);     Serial.println(F("EVT WS BLEU"));  break;
          case 3: wsOverride = strip.Color(255, 255, 255); Serial.println(F("EVT WS BLANC")); break;
          default: testEnd(false); break;
        }
      }
      break;
    }
  }
}

static void seqStepStart() {
  ledOn(seqK);
  seqT0 = millis();
  seqPhase = SEQ_ATTENTE;
  oledRefresh(true);
}

static void startSeq(uint16_t pose, uint16_t attente) {
  clearLatch();
  ledAllOff();
  seqPose = pose; seqAttente = attente; seqK = 1; seqDebut = millis();
  motorLastActive = seqDebut;
  Serial.print(F("EVT SEQ debut pose_ms=")); Serial.print(pose);
  Serial.print(F(" attente_ms="));           Serial.println(attente);
  seqStepStart();
}

static void updateSeq() {
  if (seqPhase == SEQ_OFF) return;
  uint32_t now = millis();
  if (seqPhase == SEQ_ATTENTE) {
    if ((uint32_t)(now - seqT0) >= seqAttente) {
      trigStart(); seqT1 = millis(); seqPhase = SEQ_POSE;
    }
  } else if (seqPhase == SEQ_POSE) {
    if ((uint32_t)(now - seqT1) >= (uint32_t)seqPose + SEQ_MARGE_MS) {
      ledAllOff();
      Serial.print(F("IMG ")); Serial.println(seqK);
      if (seqK >= NB_LED) {
        seqPhase = SEQ_OFF; motorLastActive = now;
        seqDone = true; seqDurMs = (uint32_t)(now - seqDebut);
        Serial.print(F("OK SEQ n=")); Serial.print(NB_LED);
        Serial.print(F(" duree_ms=")); Serial.println((uint32_t)(now - seqDebut));
      } else {
        seqPhase = SEQ_PAUSE;
      }
    }
  } else {
    if ((uint32_t)(now - seqT1) + seqAttente >= SEQ_PERIODE_MIN_MS) {
      seqK++; seqStepStart();
    }
  }
}

static void stopTout(bool depuisBouton) {
  bool actif = (seqPhase != SEQ_OFF) || (mvCmd != MC_NONE);
  seqDone = false;
  ledAllOff();
  digitalWrite(PIN_TRIG, LOW); trigActive = false;
  if (seqPhase != SEQ_OFF) {
    seqPhase = SEQ_OFF;
    Serial.print(F("ERR SEQ interrompu a la LED ")); Serial.println(seqK);
  }
  if (mvCmd != MC_NONE) {
    stepper.setCurrentPosition(stepper.currentPosition());
    errLn(mvName(), F("interrompu"));
    mvCmd = MC_NONE; mvPhase = PH_NONE; homed = false;
  }
  motorEnable(false);
  if (testMode != T_NONE) testEnd(true);
  latched = (actif || depuisBouton) ? ETAT_ARRET : ETAT_PRET;
}

static void updateLedTimeout() {
  if (ledCur && (uint32_t)(millis() - ledOnAt) >= LED_MAX_ON_MS) {
    uint8_t k = ledCur;
    ledAllOff();
    Serial.print(F("EVT LED_AUTOCUT ")); Serial.print(k);
    Serial.print(F(" on_ms=")); Serial.println((uint32_t)(millis() - ledOnAt));
    if (seqPhase != SEQ_OFF) {
      seqPhase = SEQ_OFF; latched = ETAT_ERREUR;
      errLn(F("SEQ"), F("coupure automatique 10 s"));
    }
  }
}

static void mvDone() {
  Serial.print(F("OK ")); Serial.print(mvName());
  if (mvCmd != MC_HOME) { Serial.print(' '); Serial.print(mvArg, 2); }
  Serial.print(F(" angle=")); Serial.print(angleDeg(), 2);
  Serial.print(F(" homed=")); Serial.print(homed ? 1 : 0);
  Serial.print(F(" ms="));    Serial.println((uint32_t)(millis() - mvT0));
  mvCmd = MC_NONE; mvPhase = PH_NONE; motorLastActive = millis();
}
static void mvFail(const __FlashStringHelper* msg) {
  errLn(mvName(), msg);
  stepper.setCurrentPosition(stepper.currentPosition());
  mvCmd = MC_NONE; mvPhase = PH_NONE; homed = false;
  motorEnable(false);
  latched = ETAT_ERREUR;
}

static void updateMotion() {
  if (mvCmd == MC_NONE || !motorReady()) return;
  bool arrive = (stepper.distanceToGo() == 0);
  switch (mvPhase) {
    case PH_MOVE:
      if (arrive) mvDone();
      break;
    case PH_CLEAR:
      if (!sensStable) {
        stepper.moveTo(stepper.currentPosition() - HOME_DIR * HOME_BACKOFF_STEPS);
        mvPhase = PH_BACKOFF;
      } else if (arrive) mvFail(F("capteur toujours actif apres 1,25 tour (niveau actif ?)"));
      break;
    case PH_BACKOFF:
      if (arrive) {
        stepper.moveTo(stepper.currentPosition() + HOME_DIR * HOME_MAX_STEPS);
        mvPhase = PH_SEEK;
      }
      break;
    case PH_SEEK:
      if (sensStable) {
        homeEdge = stepper.currentPosition();
        stepper.stop();
        mvPhase = PH_STOP;
      } else if (arrive) mvFail(F("capteur non trouve en 1,25 tour"));
      break;
    case PH_STOP:
      if (arrive) {
        stepper.setCurrentPosition(stepper.currentPosition() - homeEdge);
        stepper.moveTo(0);
        mvPhase = PH_RETURN;
      }
      break;
    case PH_RETURN:
      if (arrive) { homed = true; mvDone(); }
      break;
  }
}

static void updateMotorIdle() {
  if (motorOn && MOTOR_IDLE_OFF_MS && mvCmd == MC_NONE && seqPhase == SEQ_OFF &&
      (uint32_t)(millis() - motorLastActive) >= MOTOR_IDLE_OFF_MS) {
    motorEnable(false);
  }
}

static void updateSensor() {
  uint32_t now = millis();
  bool r = (digitalRead(PIN_HOME) == HOME_ACTIVE_LEVEL);
  if (r != sensRaw) { sensRaw = r; sensT = now; }
  if (sensStable != sensRaw && (uint32_t)(now - sensT) >= SENSOR_FILTER_MS) sensStable = sensRaw;
}

static void manuelSuivant() {
  clearLatch();
  uint8_t k = (ledLast % NB_LED) + 1;
  ledOn(k);
  Serial.print(F("EVT BTN SUIVANT led=")); Serial.println(k);
}

static void onButton(uint8_t i, bool pressed) {
  if (testMode == T_BOUTONS) {
    Serial.print(F("EVT BTN ")); Serial.print(BTN_NOM[i]);
    Serial.println(pressed ? F(" APPUYE") : F(" RELACHE"));
    if (pressed) btn[i].presses++;
    if (i == 2 && pressed) stopTout(true);
    return;
  }
  if (!pressed) return;
  if (i == 2) {
    Serial.println(F("EVT BTN ARRET"));
    stopTout(true);
    return;
  }
  if (testMode != T_NONE) return;
  bool occupe = (seqPhase != SEQ_OFF);
  if (i == 0) {
    if (occupe || mvCmd != MC_NONE || trigActive) {
      Serial.println(F("EVT BTN DEMARRER ignore (occupe)"));
    } else {
      Serial.println(F("EVT BTN DEMARRER"));
      startSeq(BTN_POSE_MS, SEQ_ATTENTE_DEFAUT_MS);
    }
  } else {
    if (occupe) Serial.println(F("EVT BTN SUIVANT ignore (occupe)"));
    else manuelSuivant();
  }
}

static void updateButtons() {
  uint32_t now = millis();
  const uint8_t ordre[3] = { 2, 0, 1 };
  for (uint8_t n = 0; n < 3; n++) {
    uint8_t i = ordre[n];
    bool r = (digitalRead(btn[i].pin) == LOW);
    if (r != btn[i].raw) { btn[i].raw = r; btn[i].t = now; btn[i].trans++; }
    if (btn[i].stable != btn[i].raw && (uint32_t)(now - btn[i].t) >= DEBOUNCE_MS) {
      btn[i].stable = btn[i].raw;
      onButton(i, btn[i].stable);
    }
  }
}

static void cmdHelp() {
  Serial.println(F("# HELP | STATUS | OFF"));
  Serial.println(F("# LED <1-16>            : allume une seule LED (coupure auto 10 s)"));
  Serial.println(F("# TRIG                  : impulsion de declenchement camera (D5)"));
  Serial.println(F("# SEQ <pose_ms> [att_ms]: 16 LED + declenchement, envoie IMG k, puis OK SEQ"));
  Serial.println(F("# HOME                  : cherche le capteur zero (D18)"));
  Serial.println(F("# ROT <deg>             : tourne de <deg> (relatif, +/-)"));
  Serial.println(F("# GOTO <deg>            : va a l'angle absolu (chemin le plus court)"));
  Serial.println(F("# TEST BOUTONS|CAPTEUR|OLED|WS"));
  Serial.println(F("# Boutons : Demarrer = SEQ ; Suivant = LED suivante ; Arret = OFF + moteur"));
  Serial.println(F("OK HELP"));
}

static void cmdStatus() {
  Serial.print(F("OK STATUS etat=")); Serial.print(etatAscii(deriveState()));
  Serial.print(F(" led="));    Serial.print(ledCur);
  Serial.print(F(" angle="));  Serial.print(angleDeg(), 2);
  Serial.print(F(" homed="));  Serial.print(homed ? 1 : 0);
  Serial.print(F(" moteur=")); Serial.print(motorOn ? 1 : 0);
  Serial.print(F(" capteur=")); Serial.print(sensStable ? F("OCCULTE") : F("LIBRE"));
  Serial.print(F(" oled="));   Serial.print(oledOk ? 1 : 0);
  Serial.print(F(" oled_ms=")); Serial.print(oledDurMs);
  Serial.print(F(" seq="));    Serial.print(seqPhase != SEQ_OFF ? seqK : 0);
  Serial.print(F(" test="));   Serial.print(testMode != T_NONE ? 1 : 0);
  Serial.print(F(" up_ms="));  Serial.println(millis());
}

static void cmdLed(char** tok, uint8_t n) {
  long k;
  if (n != 2 || !parseLong(tok[1], k)) { errLn(F("LED"), F("syntaxe : LED <1-16>")); return; }
  if (k < 1 || k > NB_LED)             { errLn(F("LED"), F("numero hors limites (1-16)")); return; }
  if (seqPhase != SEQ_OFF)             { errLn(F("LED"), F("occupe (SEQ en cours)")); return; }
  if (testMode != T_NONE)              { errLn(F("LED"), F("occupe (essai en cours, OFF pour quitter)")); return; }
  clearLatch();
  ledOn((uint8_t)k);
  Serial.print(F("OK LED ")); Serial.println(k);
}

static void cmdTrig(uint8_t n) {
  if (n != 1)                          { errLn(F("TRIG"), F("syntaxe : TRIG")); return; }
  if (seqPhase != SEQ_OFF)             { errLn(F("TRIG"), F("occupe (SEQ en cours)")); return; }
  if (testMode != T_NONE)              { errLn(F("TRIG"), F("occupe (essai en cours)")); return; }
  if (trigActive)                      { errLn(F("TRIG"), F("occupe (impulsion en cours)")); return; }
  clearLatch();
  trigStart();
  Serial.println(F("OK TRIG"));
}

static void cmdSeq(char** tok, uint8_t n) {
  long pose, att = SEQ_ATTENTE_DEFAUT_MS;
  if (n < 2 || n > 3 || !parseLong(tok[1], pose) || (n == 3 && !parseLong(tok[2], att))) {
    errLn(F("SEQ"), F("syntaxe : SEQ <pose_ms> [attente_ms]")); return;
  }
  if (att < 0 || att > SEQ_ATTENTE_MAX_MS) { errLn(F("SEQ"), F("attente_ms hors limites (0-2000)")); return; }
  long poseMax = (long)LED_MAX_ON_MS - SEQ_RESERVE_MS - att - SEQ_MARGE_MS;
  if (pose < 1 || pose > poseMax) {
    Serial.print(F("ERR SEQ pose_ms hors limites (1-")); Serial.print(poseMax); Serial.println(')'); return;
  }
  if (seqPhase != SEQ_OFF || mvCmd != MC_NONE || trigActive) { errLn(F("SEQ"), F("occupe")); return; }
  if (testMode != T_NONE)              { errLn(F("SEQ"), F("occupe (essai en cours)")); return; }
  startSeq((uint16_t)pose, (uint16_t)att);
}

static bool refuseMouvement(const __FlashStringHelper* cmd) {
  if (seqPhase != SEQ_OFF) { errLn(cmd, F("occupe (SEQ en cours)")); return true; }
  if (testMode != T_NONE)  { errLn(cmd, F("occupe (essai en cours)")); return true; }
  if (mvCmd != MC_NONE)    { errLn(cmd, F("occupe (moteur en mouvement)")); return true; }
  return false;
}

static void beginMove(uint8_t cmd, float arg, long steps) {
  clearLatch();
  stepper.setMaxSpeed(ROT_VMAX); stepper.setAcceleration(ROT_ACCEL);
  mvCmd = cmd; mvArg = arg; mvPhase = PH_MOVE; mvT0 = millis();
  motorEnable(true);
  stepper.move(steps);
  oledRefresh(true);
}

static void cmdHome(uint8_t n) {
  if (n != 1) { errLn(F("HOME"), F("syntaxe : HOME")); return; }
  if (refuseMouvement(F("HOME"))) return;
  clearLatch();
  stepper.setMaxSpeed(HOME_SPEED); stepper.setAcceleration(HOME_ACCEL);
  mvCmd = MC_HOME; mvArg = 0; mvT0 = millis();
  motorEnable(true);
  if (sensStable) {
    stepper.moveTo(stepper.currentPosition() - HOME_DIR * HOME_MAX_STEPS);
    mvPhase = PH_CLEAR;
  } else {
    stepper.moveTo(stepper.currentPosition() + HOME_DIR * HOME_MAX_STEPS);
    mvPhase = PH_SEEK;
  }
  oledRefresh(true);
}

static void cmdRot(char** tok, uint8_t n) {
  float deg;
  if (n != 2 || !parseFloat(tok[1], deg)) { errLn(F("ROT"), F("syntaxe : ROT <deg>")); return; }
  if (!(deg >= -720.0f && deg <= 720.0f)) { errLn(F("ROT"), F("angle hors limites (-720 a 720)")); return; }
  if (refuseMouvement(F("ROT"))) return;
  long steps = roundL(deg * ((float)STEPS_PER_REV / 360.0f));
  if (steps == 0) { Serial.print(F("OK ROT 0.00 angle=")); Serial.print(angleDeg(), 2); Serial.print(F(" homed=")); Serial.print(homed ? 1 : 0); Serial.println(F(" ms=0")); return; }
  beginMove(MC_ROT, deg, steps);
}

static void cmdGoto(char** tok, uint8_t n) {
  float deg;
  if (n != 2 || !parseFloat(tok[1], deg)) { errLn(F("GOTO"), F("syntaxe : GOTO <deg>")); return; }
  if (!(deg >= -720.0f && deg <= 720.0f)) { errLn(F("GOTO"), F("angle hors limites (-720 a 720)")); return; }
  if (refuseMouvement(F("GOTO"))) return;
  long cible = normSteps(roundL(deg * ((float)STEPS_PER_REV / 360.0f)));
  long delta = cible - posMod();
  if (delta > STEPS_PER_REV / 2) delta -= STEPS_PER_REV;
  else if (delta < -(STEPS_PER_REV / 2)) delta += STEPS_PER_REV;
  if (delta == 0) { Serial.print(F("OK GOTO ")); Serial.print(deg, 2); Serial.print(F(" angle=")); Serial.print(angleDeg(), 2); Serial.print(F(" homed=")); Serial.print(homed ? 1 : 0); Serial.println(F(" ms=0")); return; }
  beginMove(MC_GOTO, deg, delta);
}

static void cmdTest(char** tok, uint8_t n) {
  if (n != 2) { errLn(F("TEST"), F("syntaxe : TEST BOUTONS|CAPTEUR|OLED|WS")); return; }
  uint8_t mode;
  if      (!strcmp(tok[1], "BOUTONS")) mode = T_BOUTONS;
  else if (!strcmp(tok[1], "CAPTEUR")) mode = T_CAPTEUR;
  else if (!strcmp(tok[1], "OLED"))    mode = T_OLED;
  else if (!strcmp(tok[1], "WS"))      mode = T_WS;
  else { errLn(F("TEST"), F("essai inconnu (BOUTONS, CAPTEUR, OLED, WS)")); return; }
  if (seqPhase != SEQ_OFF || mvCmd != MC_NONE) { errLn(F("TEST"), F("occupe")); return; }
  if (testMode != T_NONE)                      { errLn(F("TEST"), F("occupe (essai en cours, OFF pour quitter)")); return; }
  if (mode == T_OLED && !oledOk) {
    errLn(F("TEST"), F("OLED non detecte a l'adresse I2C 0x3C (voir TESTS.md, bloc 6)")); return;
  }
  testStart(mode);
}

static void handleLine(char* line) {
  for (char* p = line; *p; ++p) *p = toupper((unsigned char)*p);
  char* tok[5]; uint8_t n = 0; char* save;
  for (char* t = strtok_r(line, " \t", &save); t && n < 5; t = strtok_r(NULL, " \t", &save)) tok[n++] = t;
  if (n == 0) return;
  const char* c = tok[0];

  if (!strcmp(c, "HELP"))        cmdHelp();
  else if (!strcmp(c, "STATUS")) cmdStatus();
  else if (!strcmp(c, "OFF")) {
    stopTout(false);
    Serial.println(F("OK OFF"));
  }
  else if (!strcmp(c, "LED"))    cmdLed(tok, n);
  else if (!strcmp(c, "TRIG"))   cmdTrig(n);
  else if (!strcmp(c, "SEQ"))    cmdSeq(tok, n);
  else if (!strcmp(c, "HOME"))   cmdHome(n);
  else if (!strcmp(c, "ROT"))    cmdRot(tok, n);
  else if (!strcmp(c, "GOTO"))   cmdGoto(tok, n);
  else if (!strcmp(c, "TEST"))   cmdTest(tok, n);
  else { Serial.print(F("ERR ")); Serial.print(c); Serial.println(F(" commande inconnue (HELP)")); }
}

static void readSerial() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      bool over = rxOver; uint8_t len = rxN;
      rxN = 0; rxOver = false;
      if (over) { Serial.println(F("ERR ? ligne trop longue (63 caracteres max)")); }
      else if (len > 0) { rx[len] = 0; handleLine(rx); }
      return;
    }
    if (rxN < sizeof(rx) - 1) rx[rxN++] = c; else rxOver = true;
  }
}

void setup() {

  for (uint8_t k = 1; k <= NB_LED; k++) { digitalWrite(ledPin(k), LOW); pinMode(ledPin(k), OUTPUT); }
  digitalWrite(PIN_EN, HIGH);   pinMode(PIN_EN, OUTPUT);
  digitalWrite(PIN_TRIG, LOW);  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_BTN_START, INPUT_PULLUP);
  pinMode(PIN_BTN_NEXT,  INPUT_PULLUP);
  pinMode(PIN_BTN_STOP,  INPUT_PULLUP);
  pinMode(PIN_HOME,      INPUT_PULLUP);

  Serial.begin(115200);

  stepper.setPinsInverted(DIR_INVERSE, false, false);
  stepper.setMinPulseWidth(3);
  stepper.setMaxSpeed(ROT_VMAX);
  stepper.setAcceleration(ROT_ACCEL);
  stepper.setCurrentPosition(0);

  uint32_t now = millis();
  for (uint8_t i = 0; i < 3; i++) { btn[i].raw = btn[i].stable = (digitalRead(btn[i].pin) == LOW); btn[i].t = now; }
  sensRaw = sensStable = (digitalRead(PIN_HOME) == HOME_ACTIVE_LEVEL); sensT = now;

  strip.begin();
  strip.setBrightness(WS_LUMINOSITE);
  strip.setPixelColor(0, 0); strip.show();

  Wire.begin();
#if defined(WIRE_HAS_TIMEOUT)
  Wire.setWireTimeout(3000, true);
#endif
  u8g2.setI2CAddress(OLED_I2C_ADDR << 1);
  u8g2.begin();

  digitalWrite(SDA, LOW);
  digitalWrite(SCL, LOW);
  Wire.beginTransmission(OLED_I2C_ADDR);
  oledOk = (Wire.endTransmission() == 0);
  if (oledOk) { u8g2.setBusClock(400000); u8g2.enableUTF8Print(); oledSplash(); }
  oledInvalidate();
  oledRefresh(true);
  wsUpdate();

  motorLastActive = millis();
  Serial.print(F("EVT BOOT dome_ps16 v" FW_VERSION " oled="));
  Serial.println(oledOk ? 1 : 0);
}

void loop() {
  if (mvCmd != MC_NONE && motorReady()) stepper.run();
  updateButtons();
  readSerial();
  updateSensor();
  updateLedTimeout();
  updateTrig();
  updateSeq();
  updateMotion();
  updateTest();
  updateMotorIdle();
  wsUpdate();
  if (oledAllowed()) oledRefresh(false);
}
