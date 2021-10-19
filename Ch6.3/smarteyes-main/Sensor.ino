#include "Ultrasonic.h"
 
Ultrasonic ultrasonic(7);
void setup()
{
    Serial.begin(9600);
}
void loop()
{
    long RangeInCentimeters;
 
    RangeInCentimeters = ultrasonic.MeasureInCentimeters(); // two measurements should keep an interval
    Serial.print("Distance: "); 
    Serial.println(RangeInCentimeters);//0~400cm
    delay(1000);
    float l = analogRead(A0);
    Serial.print("Light value: ");
    Serial.println(l);
    delay(1000);
}
