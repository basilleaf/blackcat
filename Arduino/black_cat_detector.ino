// this runs on the Arduino

int lightPin = 0;  //define a pin for Photo resistor
int avgRead;  // place holder for average

void setup()
{
  Serial.begin(9600);
}

void loop(){
    getReading(5);
    delay(1000);
 }

void getReading(int times){
    int reading;
    int tally=0;
    //take the reading however many times was requested and add them up
    for(int i = 0;i < times;i++){
        reading = analogRead(lightPin);
        tally = reading + tally;
        delay(10);
    }
    //calculate the average and set it
    avgRead = (tally)/times;
    Serial.println(avgRead);

}
