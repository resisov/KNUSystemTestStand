//
//  Run Configurations
//
double   _runNumber  ;           // run number
char     _RunType[64] ;          // store ,  dummy
char     _RunFeature[64] ;       // if you don't want RunTag, put no, otherwise put anything you want. 
char     _sID[64]   ;            // sensor ID
double   _radiation ;            // 0 = no ,  1 = irradiated
double   _amp  ;                 // 0 = no amp ,   1 = amp
double   _measurementType ;      // 1 = laser, 2 = source, 3 = IV , 4 = CV
double   _biasVoltage ;          // [V]
double   _source ;               // 0 : Sr90,  1 : laser
double   _trigger_type ;         // 1 : edge,  2 : glitch
double   _trigger_threshold  ;   // [mV]
double   _trigger_width ;        // [ns]
double   _trigger_channel ;      // 1, 2, 3, 4
double   _Ch1_status, _Ch2_status, _Ch3_status, _Ch4_status ; // 0 : OFF,  1 : ON
double   _temperature ;          // Celcius
double   _humidity ;             // humidity
char     _daqstart[64], _daqend[64] ;    // daq time start, end
char     _memo01[64], _memo02[64], _memo03[64], _memo04[64], _memo05[64]  ; // memo
char     _memo06[64], _memo07[64], _memo08[64], _memo09[64], _memo10[64]  ; // memo
char     _memo11[64], _memo12[64], _memo13[64], _memo14[64]  ; // memo


//
//
//
TString FileRunConfig    = "Tek.run.config" ; 
TString FileRunNumber    = "Tek.runNumber.previous" ; 
TString FileDaqTimeStart = "Tek.run.time.start" ;
TString FileDaqTimeEnd   = "Tek.run.time.end" ;


void ReadConfigLineChar(ifstream &fname, const char *separator, char *var_char ) {
   TString lineString;
   TObjArray *cx ;

   lineString.ReadLine(fname);
   cx = lineString.Tokenize(separator);
   strcpy(var_char, ((TObjString *)(cx->At(1)))->String());

}

void ReadConfigLineDouble(ifstream &fname, const char *separator, double &var_double){
   TString lineString;
   TObjArray *cx ;

   lineString.ReadLine(fname);
   cx = lineString.Tokenize(separator);
   var_double = (((TObjString *)(cx->At(1)))->String()).Atof();

}

void ReadConfigLineSkip(ifstream &fname){
   TString lineString;
   lineString.ReadLine(fname);
}


void Read_RunConfig(){

   ifstream inconfig;

   //
   //   Run Configuration
   //
   inconfig.open(FileRunConfig.Data());

   ReadConfigLineChar(inconfig,   " ", _RunType);
   ReadConfigLineChar(inconfig,   " ", _RunFeature);
   ReadConfigLineChar(inconfig,   " ", _sID   );
   ReadConfigLineDouble(inconfig, " ", _radiation );
   ReadConfigLineDouble(inconfig, " ", _amp   );
   ReadConfigLineDouble(inconfig, " ", _measurementType );
   ReadConfigLineDouble(inconfig, " ", _biasVoltage );
   ReadConfigLineDouble(inconfig, " ", _source );
   ReadConfigLineDouble(inconfig, " ", _trigger_type );
   ReadConfigLineDouble(inconfig, " ", _trigger_threshold );
   ReadConfigLineDouble(inconfig, " ", _trigger_width );
   ReadConfigLineDouble(inconfig, " ", _trigger_channel );
   ReadConfigLineDouble(inconfig, " ", _Ch1_status );
   ReadConfigLineDouble(inconfig, " ", _Ch2_status );
   ReadConfigLineDouble(inconfig, " ", _Ch3_status );
   ReadConfigLineDouble(inconfig, " ", _Ch4_status );
   ReadConfigLineDouble(inconfig, " ", _temperature );
   ReadConfigLineDouble(inconfig, " ", _humidity );

   ReadConfigLineSkip(inconfig);
   ReadConfigLineSkip(inconfig);

   ReadConfigLineChar(inconfig, "|", _memo01 );
   ReadConfigLineChar(inconfig, "|", _memo02 );
   ReadConfigLineChar(inconfig, "|", _memo03 );
   ReadConfigLineChar(inconfig, "|", _memo04 );
   ReadConfigLineChar(inconfig, "|", _memo05 );
   ReadConfigLineChar(inconfig, "|", _memo06 );
   ReadConfigLineChar(inconfig, "|", _memo07 );
   ReadConfigLineChar(inconfig, "|", _memo08 );
   ReadConfigLineChar(inconfig, "|", _memo09 );
   ReadConfigLineChar(inconfig, "|", _memo10 );
   ReadConfigLineChar(inconfig, "|", _memo11 );
   ReadConfigLineChar(inconfig, "|", _memo12 );
   ReadConfigLineChar(inconfig, "|", _memo13 );
   ReadConfigLineChar(inconfig, "|", _memo14 );

   inconfig.close();
}


void getConfigValue_char(TString cfgField, char *var_char){
   TString _field;

   strcpy(var_char,  "-99999");

   _field = cfgField; 
   _field.ToLower();

   if(_field=="runtype") strcpy(var_char, _RunType); 
   if(_field=="runfeature") strcpy(var_char, _RunFeature); 
   if(_field=="sensor") strcpy(var_char, _sID); 
   if(_field=="memo01") strcpy(var_char, _memo01); 
   if(_field=="memo02") strcpy(var_char, _memo02); 
   if(_field=="memo03") strcpy(var_char, _memo03); 
   if(_field=="memo04") strcpy(var_char, _memo04); 
   if(_field=="memo05") strcpy(var_char, _memo05); 
   if(_field=="memo06") strcpy(var_char, _memo06); 
   if(_field=="memo07") strcpy(var_char, _memo07); 
   if(_field=="memo08") strcpy(var_char, _memo08); 
   if(_field=="memo09") strcpy(var_char, _memo09); 
   if(_field=="memo10") strcpy(var_char, _memo10); 
   if(_field=="memo11") strcpy(var_char, _memo11); 
   if(_field=="memo12") strcpy(var_char, _memo12); 
   if(_field=="memo13") strcpy(var_char, _memo13); 
   if(_field=="memo14") strcpy(var_char, _memo14); 
   if(_field=="daqstart") strcpy(var_char, _daqstart); 
   if(_field=="daqend")   strcpy(var_char, _daqend); 

   if( strcmp(var_char ,"-99999" ) == 0 ) cout << ">>>>  Err :  Unknown field " << cfgField << endl;

}


void getConfigValue_double(TString cfgField, double &var_double){
   TString _field;

   var_double = -99999;

   _field = cfgField;
   _field.ToLower();

   if(_field=="runnumber")         var_double = _runNumber ; 
   if(_field=="radiation")         var_double = _radiation ; 
   if(_field=="amp")               var_double = _amp ; 
   if(_field=="measurementtype")   var_double = _measurementType ; 
   if(_field=="biasvoltage")       var_double = _biasVoltage ; 
   if(_field=="source")            var_double = _source ; 
   if(_field=="trigger_type")      var_double = _trigger_type ; 
   if(_field=="trigger_threshold") var_double = _trigger_threshold ; 
   if(_field=="trigger_width")     var_double = _trigger_width ; 
   if(_field=="trigger_channel")   var_double = _trigger_channel ; 
   if(_field=="channel_1_status")  var_double = _Ch1_status ; 
   if(_field=="channel_2_status")  var_double = _Ch2_status ; 
   if(_field=="channel_3_status")  var_double = _Ch3_status ; 
   if(_field=="channel_4_status")  var_double = _Ch4_status ; 
   if(_field=="temperature")       var_double = _temperature ; 
   if(_field=="humidity")          var_double = _humidity ; 

   if(var_double == -99999) cout << ">>>>  Err :  Unknown field " << cfgField << endl;

}


void Read_CurrentRunNumber(){
   ifstream currRunFile;
   double previousRun;

   currRunFile.open(FileRunNumber.Data());
   ReadConfigLineDouble(currRunFile,  "_", previousRun);
   currRunFile.close();

   _runNumber = previousRun + 1 ;

}

void Set_NextRunNumber(){
   TString cmd;
   ofstream nextRunFile;
   double run, nextRun;

   Read_CurrentRunNumber(); 
   getConfigValue_double("RunNumber",run);

   //nextRun = run + 1;
   cmd = "rm " + FileRunNumber ;
   //gSystem->Exec("mv Tek.runNumber Tek.runNumber.old");
   gSystem->Exec(cmd.Data());
   nextRunFile.open(FileRunNumber.Data());
   nextRunFile << "run_" << run ;
   nextRunFile.close();

}


void Read_DaqTimeStart(){
   ifstream daqtime;
   daqtime.open(FileDaqTimeStart.Data());
   ReadConfigLineChar(daqtime,  "|", _daqstart);
   daqtime.close();
}

void Read_DaqTimeEnd(){
   ifstream daqtime;
   daqtime.open(FileDaqTimeEnd.Data());
   ReadConfigLineChar(daqtime,  "|", _daqend);
   daqtime.close();
}







