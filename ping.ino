const int pin1 = 7;
const int pin2 = 8;


void setup() {
  // initialize serial communication:
  Serial.begin(9600);
}

void loop() {
  // establish variables for duration of the ping, and the distance result
  // in inches and centimeters:
  long duration1, duration2, cm1, cm2;


  // The same pin is used to read the signal from the PING))): a HIGH pulse
  // whose duration is the time (in microseconds) from the sending of the ping
  // to the reception of its echo off of an object.

  duration1 = ping(pin1);
  duration2 = ping(pin2);

  cm1 = duration1*.034/2;
  cm2 = duration2*.034/2;

  Serial.print(cm1);
  Serial.print(" cm, ");
  Serial.print(cm2);
  Serial.print(" cm");
  
  Serial.println();

  delay(100);
}

int ping(int p){
  // The PING))) is triggered by a HIGH pulse of 2 or more microseconds.
  // Give a short LOW pulse beforehand to ensure a clean HIGH pulse:
  pinMode(p, OUTPUT);
  digitalWrite(p, LOW);
  delayMicroseconds(2);
  digitalWrite(p, HIGH);
  delayMicroseconds(5);
  digitalWrite(p, LOW);

  pinMode(p, INPUT);

  return pulseIn(p, HIGH);

}

