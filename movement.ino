// defines pins numbers
const int RIGHT_FWD    = 10;
const int RIGHT_BWD    = 11;
const int RIGHT_PWM    = 5;
const int LEFT_FWD     = 13;
const int LEFT_BWD     = 12;
const int LEFT_PWM     = 6;

const int SENSOR_LEFT   = 7;
const int SENSOR_RIGHT  = 8;
const int SENSOR_FRONT  = 4;
const int LEFT_SPEED    = 100;
const int RIGHT_SPEED   = .95*LEFT_SPEED;

const int SLOW_DIST     = 100;
const int OBS_DIST      = 20;

// Get this to half

void setup() {
  // initialize serial communication:
  pinMode(LEFT_FWD, OUTPUT);
  pinMode(LEFT_BWD, OUTPUT);
  pinMode(LEFT_PWM, OUTPUT);
  pinMode(RIGHT_FWD, OUTPUT);
  pinMode(RIGHT_BWD, OUTPUT);
  pinMode(RIGHT_PWM, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  // establish variables for duration of the ping, and the distance result
  // in inches and centimeters:
  long duration1, duration2, cm1, cm2;
  
  /***************************************************************************
   * MOTOR CODE
   ***************************************************************************/
  check_obstacles();
//  move_fwd(LEFT_SPEED,RIGHT_SPEED);
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

  return pulseIn(p, HIGH)*.034/2;
}

void move_fwd (int l_pwm, int r_pwm) {
  //Write the speed to the motors
  analogWrite(LEFT_PWM, abs(l_pwm));
  analogWrite(RIGHT_PWM,abs(r_pwm));

  // Determine the direction the motors should go
  digitalWrite(LEFT_FWD,  (l_pwm >= 0));
  digitalWrite(RIGHT_FWD, (r_pwm >= 0));
  digitalWrite(LEFT_BWD,  (l_pwm < 0));
  digitalWrite(RIGHT_BWD, (r_pwm < 0));
}

void check_obstacles () {
  // The same pin is used to read the signal from the PING))): a HIGH pulse
  // whose duration is the time (in microseconds) from the sending of the ping
  // to the reception of its echo off of an object.
  long duration1, duration2, l_dist, r_dist, f_dist, l_speed, r_speed;
  static int speed_count = 0;

  // Check each sensor
  l_dist = ping(SENSOR_LEFT);
  r_dist = ping(SENSOR_RIGHT);
  f_dist = ping(SENSOR_FRONT);

  // Print each measurement
  Serial.print("Left: ");
  Serial.print(l_dist);
  Serial.print(" cm, Front: ");
  Serial.print(f_dist);
  Serial.print(" cm, Right: ");
  Serial.print(r_dist);
  Serial.print(" cm");
  Serial.println();

  if (f_dist < SLOW_DIST) {
    if (speed_count < 5) {
      speed_count = speed_count + 1;
    }  

  }
  else {
    if (speed_count > 0) {
      speed_count = speed_count - 1;
    }
  }
  Serial.println(speed_count);
  l_speed = LEFT_SPEED - speed_count * 10;
  r_speed = RIGHT_SPEED - speed_count * 10;
  // If any obstacle is noticed, turn clockwise until the obstacle is gone
  if (f_dist <= OBS_DIST) {
//    move_fwd(-1*LEFT_SPEED, -1*RIGHT_SPEED);
//    delay(200);
    move_fwd(LEFT_SPEED, -1*RIGHT_SPEED);
    delay(20);
  }
  else if (l_dist <= OBS_DIST || r_dist <= OBS_DIST) {
    move_fwd(LEFT_SPEED,-1*RIGHT_SPEED);
    delay(20);
  }
  // Otherwise, move forward
  else {
    move_fwd(l_speed,r_speed);
    delay(20);
  }
  
//  move_fwd(LEFT_SPEED*(1-2*(l_dist <= OBS_DIST)),
//      RIGHT_SPEED*(1-2*(r_dist <= OBS_DIST)));
  delay(10);

}
