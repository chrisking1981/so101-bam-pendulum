// Arduino Nano 33 IoT: stream the on-board LSM6DS3 IMU over USB serial.
// Registers are written directly (no library) for 416 Hz output, +-4 g and +-1000 deg/s.
// Each new sample is sent as one text line:  t_us,gx,gy,gz,ax,ay,az   (raw int16 counts)
//   gyro: 35 mdps/LSB   accel: 0.122 mg/LSB
// Send 'i' to get an info line (WHO_AM_I, settings).
#include <Wire.h>

const uint8_t ADDR = 0x6A;
const uint8_t WHO_AM_I = 0x0F, CTRL1_XL = 0x10, CTRL2_G = 0x11, CTRL3_C = 0x12, STATUS_REG = 0x1E, OUTX_L_G = 0x22;

void wr(uint8_t reg, uint8_t val) { Wire.beginTransmission(ADDR); Wire.write(reg); Wire.write(val); Wire.endTransmission(); }
uint8_t rd(uint8_t reg) { Wire.beginTransmission(ADDR); Wire.write(reg); Wire.endTransmission(false); Wire.requestFrom(ADDR, (uint8_t)1); return Wire.read(); }

void setup() {
  Serial.begin(1000000);              // native USB: the baud rate is ignored
  Wire.begin();
  Wire.setClock(400000);
  wr(CTRL3_C, 0x01); delay(20);       // software reset
  wr(CTRL3_C, 0x44);                  // BDU = 1 (no torn reads), IF_INC = 1 (auto-increment)
  wr(CTRL1_XL, 0x68);                 // accel 416 Hz, +-4 g
  wr(CTRL2_G, 0x68);                  // gyro 416 Hz, 1000 dps
}

void loop() {
  if (Serial.available() && Serial.read() == 'i') {
    Serial.print("# LSM6DS3 WHO_AM_I=0x"); Serial.print(rd(WHO_AM_I), HEX);
    Serial.println(" odr=416Hz accel=+-4g gyro=1000dps gyro_mdps_per_lsb=35 accel_mg_per_lsb=0.122");
  }
  if ((rd(STATUS_REG) & 0x03) != 0x03) return;   // wait until both gyro and accel have a new sample
  uint32_t t = micros();
  Wire.beginTransmission(ADDR); Wire.write(OUTX_L_G); Wire.endTransmission(false);
  Wire.requestFrom(ADDR, (uint8_t)12);
  int16_t v[6];
  for (int i = 0; i < 6; i++) { uint8_t lo = Wire.read(), hi = Wire.read(); v[i] = (int16_t)(lo | (hi << 8)); }
  char buf[80];
  snprintf(buf, sizeof(buf), "%lu,%d,%d,%d,%d,%d,%d", (unsigned long)t, v[0], v[1], v[2], v[3], v[4], v[5]);
  Serial.println(buf);
}
