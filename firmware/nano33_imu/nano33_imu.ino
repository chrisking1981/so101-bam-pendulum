// Arduino Nano 33 IoT: on-board LSM6DS3 IMU over USB serial, with on-board tilt estimation.
// - 416 Hz, +-4 g, +-1000 deg/s; registers are written directly (no library).
// - At start-up (and on command 'c') the gyro bias is measured over 2 s; keep the board still.
// - A Mahony filter (gyro + accelerometer) runs at every sample and gives the "up" direction in the
//   sensor frame (unit vector; the robot's projected gravity is minus this, after the mounting rotation).
//   The accelerometer only corrects slowly (gain KP), so drivetrain vibration is filtered out.
// Each sample is one text line:
//   t_us,gx,gy,gz,ax,ay,az,ux,uy,uz
//   gx..gz: bias-corrected gyro, raw counts (35 mdps/LSB); ax..az: raw accel counts (0.122 mg/LSB);
//   ux..uz: filtered up vector x 10000.
// Commands: 'i' info line, 'c' recalibrate the gyro bias (2 s, keep still), 'k<float>' set KP.
#include <Wire.h>
#include <math.h>

const uint8_t ADDR = 0x6A;
const uint8_t WHO_AM_I = 0x0F, CTRL1_XL = 0x10, CTRL2_G = 0x11, CTRL3_C = 0x12, STATUS_REG = 0x1E, OUTX_L_G = 0x22;
const float GYRO_RAD = 0.035f * 3.14159265f / 180.0f;   // rad/s per LSB
const float ACC_G = 0.122e-3f;                          // g per LSB

float KP = 0.5f;                       // accelerometer correction gain (1/s): time constant ~2 s
float bias[3] = {0, 0, 0};             // gyro bias, counts
float q0 = 1, q1 = 0, q2 = 0, q3 = 0;  // orientation, sensor -> world
uint32_t lastUs = 0;
bool haveQ = false;

void wr(uint8_t reg, uint8_t val) { Wire.beginTransmission(ADDR); Wire.write(reg); Wire.write(val); Wire.endTransmission(); }
uint8_t rd(uint8_t reg) { Wire.beginTransmission(ADDR); Wire.write(reg); Wire.endTransmission(false); Wire.requestFrom(ADDR, (uint8_t)1); return Wire.read(); }

bool readRaw(int16_t v[6]) {
  if ((rd(STATUS_REG) & 0x03) != 0x03) return false;
  Wire.beginTransmission(ADDR); Wire.write(OUTX_L_G); Wire.endTransmission(false);
  Wire.requestFrom(ADDR, (uint8_t)12);
  for (int i = 0; i < 6; i++) { uint8_t lo = Wire.read(), hi = Wire.read(); v[i] = (int16_t)(lo | (hi << 8)); }
  return true;
}

void calibrate() {
  Serial.println("# calibrating gyro bias: keep still for 2 s");
  double s[3] = {0, 0, 0}; double a[3] = {0, 0, 0}; int n = 0; int16_t v[6];
  uint32_t t0 = millis();
  while (millis() - t0 < 2000) if (readRaw(v)) { for (int i = 0; i < 3; i++) { s[i] += v[i]; a[i] += v[i + 3]; } n++; }
  for (int i = 0; i < 3; i++) bias[i] = s[i] / n;
  // start the filter from the measured gravity direction (yaw = 0)
  float ax = a[0] / n, ay = a[1] / n, az = a[2] / n;
  float roll = atan2f(ay, az), pitch = atan2f(-ax, sqrtf(ay * ay + az * az));
  float cr = cosf(roll / 2), sr = sinf(roll / 2), cp = cosf(pitch / 2), sp = sinf(pitch / 2);
  q0 = cr * cp; q1 = sr * cp; q2 = cr * sp; q3 = -sr * sp;
  haveQ = true; lastUs = micros();
  Serial.print("# gyro bias counts "); Serial.print(bias[0], 1); Serial.print(" "); Serial.print(bias[1], 1); Serial.print(" "); Serial.print(bias[2], 1);
  Serial.print(" from "); Serial.print(n); Serial.println(" samples");
}

void mahony(float gx, float gy, float gz, float ax, float ay, float az, float dt) {
  float an = sqrtf(ax * ax + ay * ay + az * az);
  if (an > 0.85f && an < 1.15f) {                       // only trust the accelerometer near 1 g
    ax /= an; ay /= an; az /= an;
    float vx = 2 * (q1 * q3 - q0 * q2), vy = 2 * (q0 * q1 + q2 * q3), vz = q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3;  // estimated up
    float ex = ay * vz - az * vy, ey = az * vx - ax * vz, ez = ax * vy - ay * vx;
    gx += KP * ex; gy += KP * ey; gz += KP * ez;
  }
  float h = 0.5f * dt;
  float a0 = q0, a1 = q1, a2 = q2;
  q0 += (-a1 * gx - a2 * gy - q3 * gz) * h;
  q1 += (a0 * gx + a2 * gz - q3 * gy) * h;
  q2 += (a0 * gy - a1 * gz + q3 * gx) * h;
  q3 += (a0 * gz + a1 * gy - a2 * gx) * h;
  float n = 1.0f / sqrtf(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3);
  q0 *= n; q1 *= n; q2 *= n; q3 *= n;
}

void setup() {
  Serial.begin(1000000);
  Wire.begin(); Wire.setClock(400000);
  wr(CTRL3_C, 0x01); delay(20);
  wr(CTRL3_C, 0x44);       // BDU, auto-increment
  wr(CTRL1_XL, 0x68);      // accel 416 Hz, +-4 g
  wr(CTRL2_G, 0x68);       // gyro 416 Hz, 1000 dps
  delay(200);
  calibrate();
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 'i') { Serial.print("# LSM6DS3 WHO_AM_I=0x"); Serial.print(rd(WHO_AM_I), HEX); Serial.print(" odr=416Hz mahony KP="); Serial.println(KP, 3); }
    else if (c == 'c') calibrate();
    else if (c == 'k') { KP = Serial.parseFloat(); Serial.print("# KP="); Serial.println(KP, 3); }
  }
  int16_t v[6];
  if (!readRaw(v)) return;
  uint32_t t = micros();
  float dt = (t - lastUs) * 1e-6f; lastUs = t;
  if (dt <= 0 || dt > 0.05f) dt = 1.0f / 416;
  float g[3]; for (int i = 0; i < 3; i++) g[i] = v[i] - bias[i];
  mahony(g[0] * GYRO_RAD, g[1] * GYRO_RAD, g[2] * GYRO_RAD, v[3] * ACC_G, v[4] * ACC_G, v[5] * ACC_G, dt);
  float ux = 2 * (q1 * q3 - q0 * q2), uy = 2 * (q0 * q1 + q2 * q3), uz = q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3;
  char buf[120];
  snprintf(buf, sizeof(buf), "%lu,%d,%d,%d,%d,%d,%d,%d,%d,%d", (unsigned long)t, (int)lroundf(g[0]), (int)lroundf(g[1]), (int)lroundf(g[2]),
           v[3], v[4], v[5], (int)lroundf(ux * 10000), (int)lroundf(uy * 10000), (int)lroundf(uz * 10000));
  Serial.println(buf);
}
