// defines pins numbers
const int RIGHT_FWD    = 12;
const int RIGHT_BWD    = 13;
const int RIGHT_PWM    = 5;
const int LEFT_FWD     = 11;
const int LEFT_BWD     = 10;
const int LEFT_PWM     = 6;

const int CAMERA_LIGHT  = 2;
const int SENSOR_LEFT   = 7;
const int SENSOR_RIGHT  = 8;
const int SENSOR_FRONT  = 4;
const int LEFT_SPEED    = 100*.70;
const int RIGHT_SPEED   = LEFT_SPEED;

const int SLOW_DIST     = 100;
const int OBS_DIST      = 30;
const int SIDE_DIST     = 20;

const int SLOW_TIME     = 15;
const int MIN_SPEED     = 50;

int incomingByte = 0;
int buf = 0;

const int STOP_CMD    = 0;
const int FWD_CMD     = 1;
const int LEFT_CMD    = 2;
const int RIGHT_CMD   = 3;
const int WANDER_CMD  = 4;

void setup() {
  // initialize serial communication:
  pinMode(LEFT_FWD, OUTPUT);
  pinMode(LEFT_BWD, OUTPUT);
  pinMode(LEFT_PWM, OUTPUT);
  pinMode(RIGHT_FWD, OUTPUT);
  pinMode(RIGHT_BWD, OUTPUT);
  pinMode(RIGHT_PWM, OUTPUT);
  pinMode(13, OUTPUT);

  Serial.begin(9600);
}

void loop() {
    // put your main code here, to run repeatedly:
  incomingByte = Serial.read();
  if (incomingByte == -1) {
    incomingByte = buf;
  }

  switch (incomingByte) {
    case STOP_CMD:
      move_fwd(0,0);
      break;
    case FWD_CMD:
      move_fwd(LEFT_SPEED,RIGHT_SPEED);
      break;
    case LEFT_CMD:
      turn_left(LEFT_SPEED,RIGHT_SPEED);
      break;
    case RIGHT_CMD:
      turn_right(.7*LEFT_SPEED,.7*RIGHT_SPEED);
      break;
    case WANDER_CMD:
      check_obstacles();
      break;
    case 6:
      digitalWrite(CAMERA_LIGHT, HIGH); // turn camrea LED on
    case 7:
      digitalWrite(CAMERA_LIGHT, LOW);
    default:
      break;
  }
  buf = incomingByte;
  delay(5);
}


/**************************************************************************************
* Function for running the 3-pin ping sensors
**************************************************************************************/
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

/**************************************************************************************
* Functions for controlling the motors
**************************************************************************************/
// Tell Twitch to turn to the right at a given speed
void turn_right(int l_pwm, int r_pwm) {
  move_fwd(l_pwm,-1 * r_pwm);
}

// Tell Twitch to turn to the left at a given speed
void turn_left(int l_pwm, int r_pwm) {
  move_fwd(-1*l_pwm,r_pwm);
}

// Tell Twitch to move the motors at a specific speed and direction
void move_fwd (int l_pwm, int r_pwm) {
  //Write the speed to the motors
  analogWrite(LEFT_PWM, abs(l_pwm));
  analogWrite(RIGHT_PWM,abs(r_pwm));

  // Determine the direction the motors should go
  // If the given speed was positive, move forward
  digitalWrite(LEFT_FWD,  (l_pwm >= 0));
  digitalWrite(RIGHT_FWD, (r_pwm >= 0));
  // If the given speed was negative, move backwards
  digitalWrite(LEFT_BWD,  (l_pwm < 0));
  digitalWrite(RIGHT_BWD, (r_pwm < 0));
}


/**************************************************************************************
* Function for determining movement
**************************************************************************************/
void check_obstacles () {
  // Variables for distance from obstacles
  long l_dist, r_dist, f_dist;
  bool F_OBS, R_OBS, L_OBS;

  // Variables for speed of motors
  long l_speed, r_speed;
  static int speed_count = 0;
  // Variables to track how many times we've turned or moved forward
  static int left_turns=0, right_turns=0,forward_moves=0;
  
  // Check each sensor
  l_dist = ping(SENSOR_LEFT);
  f_dist = ping(SENSOR_FRONT);
  r_dist = ping(SENSOR_RIGHT);

  // Check if we're in "danger zone" on any sensor
  F_OBS = f_dist < OBS_DIST;
  L_OBS = l_dist < SIDE_DIST;
  R_OBS = r_dist < SIDE_DIST;

  // Check if we should start slowing down
  if (f_dist < SLOW_DIST) {
    if (speed_count < SLOW_TIME) {
      // If we are coming up on an obstacle and not at min speed, slow down
      speed_count = speed_count + 1;
    }  
  }
  else {
    if (speed_count > 0) {
      // Otherwise, start speeding back up to max speed
      speed_count = speed_count - 1;
    }
  }

  // Set the speeds based on speed count
  l_speed = LEFT_SPEED  - speed_count * (LEFT_SPEED-MIN_SPEED)/SLOW_TIME;
  r_speed = RIGHT_SPEED - speed_count *(RIGHT_SPEED-MIN_SPEED)/SLOW_TIME;
  
  // Obstacle seen on JUST the right sensor, so we turn left
  if (R_OBS & !(L_OBS | F_OBS)) {
    turn_left(l_speed,r_speed);
    // Track how many times we've turned left
    left_turns = left_turns + 1;
    // Reset number of times we've moved forward
    forward_moves = 0;
    delay(40);
  }
  // Obstacle seen on JUST the left sensor, so we turn right
  else if (L_OBS & !(R_OBS | F_OBS)) {
    turn_right(l_speed,r_speed);
    // Track how many times we've turned right
    right_turns = right_turns + 1;
    // Reset number of times we've moved forward
    forward_moves = 0;
    delay(40);
  }
  // Obstacle seen on JUST the front sensor, so we turn left
  else if (F_OBS & !(R_OBS | L_OBS)) {
    turn_left(l_speed,r_speed);
    // Track how many times we've turned left
    left_turns = left_turns + 1;
    // Reset number of times we've moved forward
    forward_moves = 0;
    delay(60);
  }
  // If an obstacle is detected on MORE than one sensor, turn right
  else if (L_OBS | F_OBS | R_OBS) {
    turn_right(l_speed,r_speed);
    // Track how many times we've turned right
    right_turns = right_turns + 1;
    // Reset number of times we've move forward
    forward_moves = 0;
    delay(40);
  }
  // No obstacles detected, move forward
  else {
    move_fwd(l_speed,r_speed);
    // Keep track of how many times we've moved forward
    forward_moves = forward_moves + 1;
    delay(20);
  }

  // We've moved forward more than ten times, decide we aren't stuck
  if (forward_moves > 10) {
    // Reset all the state variables
    forward_moves = 0;
    left_turns = 0;
    right_turns = 0;
  }
  // We've been turning left and right repeatedly, we're probably stuck
  if (left_turns > 5 & right_turns > 5) {
    // Turn right for a long time
    turn_right(l_speed,r_speed);
    // Completely reset the variables
    left_turns = 0;
    right_turns = 0;
    delay(1000);
  }
}
