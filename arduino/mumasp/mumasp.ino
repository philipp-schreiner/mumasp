// MuMaSP firmware
#define VERSION "MuMaSP V0.05  22 January 2026 by Markus Friedl (markus.friedl@oeaw.ac.at)"
#define HELP "\nCommand:	Meaning:	Return value:\n?	Display version and help		(lots of text)\na	Read analog inputs 0..3 (Vadjust for PMs)	4 comma-separated integer values of 14 bits (0..16383 = 0..5V)\ncA	Calibrate axis A (0|1)	0=ok, -1/-2=wrong argument, -3=end switch problem\ne	Read end switch status	2 comma-separated boolean values (0=not engaged, 1=engaged)\nmA,P	Move axis A (0|1) to position P	(0..799 = 0..360°)	0=ok, -1/-2/-3=wrong argument(s)\nr	Read RTC date/time	Year,Month,Day,Hour,Minute,Second\nsY,M,D,H,M,S	Set RTS date/time (arguments have the same format as output of 'r')	0=ok, -1/-2=wrong argument(s)\nx	Clear list of muon hits in memory	0\nn	Read number of muon hits in memory	N\nh	Read list of muon hit timestamps (Unix time) and clear list in memory	First line: N, followed by N unix time stamps (one per line)"

#include <Ethernet.h>
#include <DS3231.h>
#include <Wire.h>
#include <time.h>
#include <AccelStepper.h> // docs: https://www.airspayce.com/mikem/arduino/AccelStepper/index.html

#define LED_red   0
#define LED_green 1
#define MUON  2
#define END1  3
#define END2  5
#define DIR1  6
#define CLK1  7 // PUL1
#define DIR2  8
#define CLK2  9 // PUL2

#define STEPS    12800   // number of turns for full circle (360°)
#define MAXSPEED   600   // steps/s
#define ACC        400   // steps/s^2
#define MAXMUONS  1000   // maximum number of muon hit timestamps to record

const unsigned char es[2] = {END1, END2}; // states of end switches


unsigned int muons = 0;          // number of hits in list
uint32_t timestamps[MAXMUONS];   // unix timestamps of muon hits

AccelStepper steppers[2] = {
  AccelStepper(AccelStepper::DRIVER, CLK1, DIR1),
  AccelStepper(AccelStepper::DRIVER, CLK2, DIR2)
};

//
// Ethernet connectivity
//
byte ip_mac[6] = { 0xDE, 0xAD, 0xBE, 0xEF, 4, 99 };
byte ip_ip[4]  = { 192, 168,  99,  99 };
byte ip_dns[4] = { 192, 168,  99,   1 };
byte ip_gw[4]  = { 192, 168,  99,   1 };
byte ip_net[4] = { 255, 255, 255,   0 };
unsigned short ip_port = 1033;

IPAddress ip(ip_ip[0], ip_ip[1], ip_ip[2], ip_ip[3]);
IPAddress myDns(ip_dns[0], ip_dns[1], ip_dns[2], ip_dns[3]);
IPAddress gateway(ip_gw[0], ip_gw[1], ip_gw[2], ip_gw[3]);
IPAddress subnet(ip_net[0], ip_net[1], ip_net[2], ip_net[3]);
EthernetServer server(ip_port);             // listening port

DS3231 myRTC;

volatile bool irqFlag = false;



void muondetected()
{
   digitalWrite(LED_red, HIGH);
   irqFlag = true;
}

int calibrate(unsigned char axis)
{
   int i;
   unsigned char e = digitalRead(es[axis]);

   // rotate back if end switch is engaged
   if (e)
   {
      // rotate clockwise until switch is not engaged anymore
      // (but at most two nineth of a turn)
      steppers[axis].move(-2*STEPS/9);
      while ((steppers[axis].distanceToGo() != 0) && e) {
         steppers[axis].run();

         e = digitalRead(es[axis]);
      }
      steppers[axis].stop();

      if (e) {
         return -3;
      }
   }

   // rotate counter-clockwise until switch is engaged
   // (but at most two nineth of a turn)
   steppers[axis].move(2*STEPS/9);
   while ( (steppers[axis].distanceToGo() != 0) && !e ) {
      steppers[axis].run();
      e = digitalRead(es[axis]);
      if (e) {
         // remember position where magnet engaged
         i = steppers[axis].currentPosition();
      }
   }
   // move for another 10° to reach parallel position
   while ( 
      (steppers[axis].distanceToGo() != 0)
      && (steppers[axis].currentPosition() - i < (STEPS*10/360))
      ) {
      steppers[axis].run();
   }
   steppers[axis].stop();
   e = digitalRead(es[axis]);

   if (e) {
      steppers[axis].setCurrentPosition(0);
   } else {
      return -3;
   }

   return 0;
}


void setangle(unsigned char axis, unsigned int position)
{
   if ( axis == 0 ) {
      // move clockwise
      steppers[axis].runToNewPosition( -( position % STEPS ) );
   } else {
      // move counter-clockwise with 90° offset
      steppers[axis].runToNewPosition( ( position % ( STEPS/2 ) ) - STEPS/4 );
   }
}

void setup() 
{
   //Serial.begin(9600);   // for debugging

   analogReadResolution(14);       // set 14 bit resolution

   pinMode(DIR1, OUTPUT);
   pinMode(CLK1, OUTPUT);
   pinMode(DIR2, OUTPUT);
   pinMode(CLK2, OUTPUT);
   pinMode(LED_red, OUTPUT);
   pinMode(LED_green, OUTPUT);

   digitalWrite(DIR1, LOW);
   digitalWrite(CLK1, HIGH);
   digitalWrite(DIR2, LOW);
   digitalWrite(CLK2, HIGH);

   // stepping motors
   steppers[0].setMaxSpeed(MAXSPEED);
   steppers[0].setAcceleration(ACC);
   steppers[1].setMaxSpeed(MAXSPEED);
   steppers[1].setAcceleration(ACC);


   // initialize the ethernet device 
   Ethernet.begin(ip_mac, ip, myDns);
   Ethernet.setLocalIP(ip);
   Ethernet.setGatewayIP(gateway);
   Ethernet.setSubnetMask(subnet);

   // light up both LEDs  
   digitalWrite(LED_red, HIGH);
   digitalWrite(LED_green, HIGH);

   delay(2000);
  
   // start listening for clients
   server.begin();

   Wire.begin();

   // clear LEDs
   digitalWrite(LED_red, LOW);
   digitalWrite(LED_green, LOW);

   attachInterrupt(digitalPinToInterrupt(MUON), muondetected, RISING);
}

void loop() 
{
   int i;
   unsigned int year, month, day, hour, minute, second;
   char stringa[30];
   DateTime now;


   if (irqFlag)
   {
      // store unix time
      if (muons<MAXMUONS)
      {
         now = RTClib::now();
         timestamps[muons]=now.unixtime();
         muons++;
         digitalWrite(LED_red, LOW);
      }
      irqFlag=0;
   }

   // wait for a new client:
   EthernetClient client = server.available();

   // when the client sends the first byte, say hello:
   if (client) 
   {
      if (client.available() > 0) 
      {
         // turn green LED on
         digitalWrite(LED_green, HIGH);

         // read the bytes incoming from the client:
         int cr = client.read();
         if (cr>0)
         {
            char thisChar = cr;
          
            switch(thisChar)
            {
               case '?':   // help
                  client.println(VERSION);
                  client.println(HELP);
                  break;
               case 'a':   // read analog inputs 0..3
                  for (i=0; i<4; i++)
                  {
                     client.print(analogRead(i));
                     if (i<3)
                     {
                        client.print(",");
                     }
                     else
                     {
                        client.println();
                     }
                  }
                  break;
               case 'c':   // calibrate axis
                  stringa[0]=0;
                  cr=client.available();
                  if (cr<1)
                  {
                     client.println("-1");
                  }
                  else
                  {
                     i=client.read()-'0';
                     if ((i==0) || (i==1))
                     {
                        client.println(calibrate(i), DEC);
                     }
                     else
                     {
                        client.println("-2");
                     }
                  }
                  break;
               case 'e':   // read end switch status
                  client.print(digitalRead(END1), DEC);
                  client.print(',');
                  client.println(digitalRead(END2), DEC);
                  break;
               case 'm':   // move axis to specific angle
                  stringa[0]=0;
                  cr=client.available();
                  if ((cr==0) || (cr>10))
                  {
                     client.println("-1");
                  }
                  else
                  {
                     for (i=0; i<cr; i++)
                     {
                        stringa[i]=client.read();
                     }
                     stringa[cr]=0;  // axis, position (0..799)
                     if (sscanf(stringa,"%d,%d",&i,&second)==2)
                     {
                        if (((i==0) || (i==1)) && (second<=STEPS-1))
                        {
                           setangle(i,second);
                           client.println("0");
                        }
                        else
                        {
                           client.println("-3");
                        }
                     }
                     else
                     {
                        client.println("-2");
                     }
                  }
                  break;
               case 'r':   // read RTC date/time
                  now = RTClib::now();
                  client.print(now.year(), DEC);
                  client.print(',');
                  client.print(now.month(), DEC);
                  client.print(',');
                  client.print(now.day(), DEC);
                  client.print(",");
                  //client.print(daysOfTheWeek[now.dayOfTheWeek()]);
                  //client.print(",");
                  client.print(now.hour(), DEC);
                  client.print(',');
                  client.print(now.minute(), DEC);
                  client.print(',');
                  client.println(now.second(), DEC);
                  break;
               case 's':   // set RTC date/time
                  stringa[0]=0;
                  cr=client.available();
                  if ((cr==0) || (cr>29))
                  {
                     client.println("-1");
                  }
                  else
                  {
                     for (i=0; i<cr; i++)
                     {
                        stringa[i]=client.read();
                     }
                     stringa[cr]=0;  // year, month, day, hour, minute, second
                     if (sscanf(stringa,"%d,%d,%d,%d,%d,%d",&year,&month,&day,&hour,&minute,&second)==6)
                     {
                        //rtc.adjust(DateTime(year, month, day, hour, minute, second));
                        myRTC.setSecond(second);
                        myRTC.setMinute(minute);
                        myRTC.setHour(hour);
                        myRTC.setDate(day);
                        myRTC.setMonth(month);
                        myRTC.setYear(year-2000);
                        client.println("0");
                     }
                     else
                     {
                        client.println("-2");
                     }
                  }
                  break;
               case 'x':    // clear list of muon hits
                  muons = 0;
                  digitalWrite(LED_red, LOW);
                  client.println("0");
                  break;
               case 'n':    // read number of muon hits in memory
                  client.println(muons, DEC);
                  break;
               case 'h':    // read list of muon hits (and clear list in memory)
                  client.println(muons, DEC);
                  for (i=0; i<muons; i++)
                  {
                     client.println(timestamps[i], DEC);
                  }
                  muons=0;
                  digitalWrite(LED_red, LOW);
                  break;
            }
         }

         // close connection
         client.stop();

         // turn green LED off
         digitalWrite(LED_green, LOW);
      }
   }

}
