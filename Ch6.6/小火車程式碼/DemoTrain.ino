#include <SparkFun_TB6612.h>

#define STBY PB1 // 「待機」控制接Arduino的11腳
#define AIN1 PB0 // 控制輸入A1
#define AIN2 PA7 // 控制輸入A2
#define PWMA PA6
#define pinAlarmForward PA0
#define pinAlarmBackward PA1
#define pinDetectedIndicator PC13

int alarmThresholdForward = 500;
int alarmThresholdBackward = 900;

const int offsetA = 1; // 正反轉設定A，可能值為1或-1。
char val;  // 儲存接收資料的變數
bool newMsg = false;
int sensorValue = 0;
float motor1speed = 0.0;
int t = 0;
bool ignore = false;
int alarmMaxF = 0;
int alarmMaxB = 0;

Motor motor1 = Motor(AIN1, AIN2, PWMA, offsetA, STBY);

void flushSerial2(){
  while (Serial2.available()){
    Serial2.read();
  }
}

void checkAlarm(){
  if ((motor1speed > 0.0 && sensorValue > alarmThresholdForward) || (motor1speed < 0.0 && sensorValue > alarmThresholdForward)){
    digitalWrite(pinDetectedIndicator, LOW);
    motor1speed = 0.0;
    Serial2.print("Alarmed! Auto STOP.");
    Serial.print("Alarmed! Auto STOP.");
    sensorValue = 0;
    return;
  }
  digitalWrite(pinDetectedIndicator, HIGH);  
}

void setup()
{
  Serial.begin(9600);
  // 設定藍牙模組的連線速率
  // 如果是HC-05，請改成38400
  Serial2.begin(38400);
  Serial.print("BT is ready!");
  Serial2.print("Usage: speed[U]p, speed[D]own, [P]ark");
  pinMode(pinAlarmForward, INPUT);
  pinMode(pinAlarmBackward, INPUT);
  pinMode(pinDetectedIndicator, OUTPUT);
}

void loop()
{
  // 檢查是否有警報
  if (!ignore && motor1speed > 0){
    sensorValue = analogRead(pinAlarmForward);
    if (sensorValue > alarmMaxF){
      alarmMaxF = sensorValue;
      Serial2.print("F: "+(String)alarmMaxF);
    }
//    Serial.println(sensorValue);
  }
  else if (!ignore && motor1speed < 0){
    sensorValue = analogRead(pinAlarmBackward);
    if (sensorValue > alarmMaxB){
      alarmMaxB = sensorValue;
      Serial2.print("B: "+(String)alarmMaxB);
    }
//    Serial.println(sensorValue);
  }
  checkAlarm();
  
  motor1.drive(motor1speed*255, 1000); // 驅動馬達1 0.2倍速正轉
  // 若收到「序列埠監控視窗」的資料，則送到藍牙模組
  if (Serial.available()) {
    val = Serial.read();
    newMsg = true;
//    Serial2.print(val);
  }
  // 若收到藍牙模組的資料，則送到「序列埠監控視窗」
  if (Serial2.available()) {
    val = Serial2.read();
    newMsg = true;
//    Serial.print(val);
  }

  // 如果有收到指令
  if (newMsg){
    newMsg = false;
    switch (val){
      case 'U':
        motor1speed += 0.1;
        if (motor1speed > 1.0){
            motor1speed = 1.0;
          }
//        Serial.print("Current Speed:" + (String)(motor1speed*100) + "%");
        Serial2.print("Speed:" + (String)(motor1speed*100) + "%");
        flushSerial2();
        break;
      case 'D':
        motor1speed -= 0.1;
        if (motor1speed < -1.0){
            motor1speed = -1.0;
          }
//        Serial.print("Current Speed:" + (String)(motor1speed*100) + "%");
        Serial2.print("Speed:" + (String)(motor1speed*100) + "%");
        flushSerial2();
        break;
      case 'P':
        motor1speed = 0.0;
//        Serial.print("Current Speed:" + (String)(motor1speed*100) + "%");
        Serial2.print("Speed:" + (String)(motor1speed*100) + "%");
        flushSerial2();
        break;
      case 'I':
        ignore = true;
        break;
      case 'R':
        ignore = false;
      case 't':
        alarmThresholdForward -= 100;
        alarmThresholdBackward -= 100;
        break;
      case 'T':
        alarmThresholdForward += 100;
        alarmThresholdBackward += 100;
        break;
      case '1':
        motor1speed = 0.1;
        break;
      case '2':
        motor1speed = 0.2;
        break;
      case '3':
        motor1speed = 0.3;
        break;
      case '4':
        motor1speed = 0.4;
        break;
      case '5':
        motor1speed = 0.5;
        break;
      case '6':
        motor1speed = 0.6;
        break;
      case '7':
        motor1speed = 0.7;
        break;
      case '8':
        motor1speed = 0.8;
        break;
      case '9':
        motor1speed = 0.9;
        break;
      case 'M':
        motor1speed = 1;
        break;
//      default:
//        Serial.print("Unrecognized command: " + (String)(val));
//        Serial2.print("Unrecognized command: " + (String)(val));
//        Serial2.print("Usage: speed[U]p, speed[D]own, [P]ark");
    }
  }
  t++;
}
