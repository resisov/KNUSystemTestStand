
//
//  Local variables
//
//
TString tagRad[2] = {"PreRad", "Irrad"};
TString tagAmp[2] = {"NoAmp", "Amp" };
TString tagTyp[4] = {"laser", "Sr90", "IV", "CV" }; 

//------------------------------------------------------------------------------------
//
//  Tek TTree variables
//
TTree *daq   ;
TTree *xtime ;
TTree *wave  ;

double t1[1000], t2[1000], t3[1000], t4[1000];
double v1[1000], v2[1000], v3[1000], v4[1000];

double timeUnit1,  timeUnit2, timeUnit3, timeUnit4 ;
double evtid, voltageUnit1, voltageUnit2, voltageUnit3, voltageUnit4 ;


double   runNumber      ;       // run number
char     RunType[64]    ;       // store ,  dummy
char     RunFeature[64] ;       // if you don't want RunTag, put no, otherwise put anything you want. 
char     sID[64]   ;            // sensor ID
double   radiation ;            // 0 = no ,  1 = irradiated
double   amp  ;                 // 0 = no amp ,   1 = amp
double   measurementType ;      // 1 = laser, 2 = source, 3 = IV , 4 = CV
double   biasVoltage ;          // [V]
double   source ;               // 0 : Sr90,  1 : laser
double   trigger_type ;         // 1 : edge,  2 : glitch
double   trigger_threshold  ;   // [mV]
double   trigger_width ;        // [ns]
double   trigger_channel ;      // 1, 2, 3, 4
double   Ch1_status, Ch2_status, Ch3_status, Ch4_status ; // 0 : OFF,  1 : ON
double   temperature ;          // Celcius
double   humidity ;             // humidity
char     daqstart[64], daqend[64] ;    // daq start, end
char     memo01[64], memo02[64], memo03[64], memo04[64], memo05[64]  ; // memo
char     memo06[64], memo07[64], memo08[64], memo09[64], memo10[64]  ; // memo
char     memo11[64], memo12[64], memo13[64], memo14[64]  ; // memo
//------------------------------------------------------------------------------------




void lgadTree_wave_Define(){

  //  TTree definitions ---------------------------------------------
  //
  daq       = new TTree("daq" , "daq info");
  xtime     = new TTree("time", "time");
  wave      = new TTree("wave", "voltage");

  daq->Branch("run"               , &runNumber)    ;

  daq->Branch("RunType"           , RunType , "RunType/C") ;
  daq->Branch("RunFeature"        , RunFeature , "RunFeature/C") ;
  daq->Branch("sensorID"          , sID , "sID/C") ;
  daq->Branch("radiation"         , &radiation ) ;
  daq->Branch("amp"               , &amp ) ;
  daq->Branch("measurementType"   , &measurementType ) ;
  daq->Branch("Vb"                , &biasVoltage)  ;
  daq->Branch("source"            , &source)       ;
  daq->Branch("trigger_type"      , &trigger_type) ;
  daq->Branch("trigger_threshold" , &trigger_threshold) ;
  daq->Branch("trigger_width"     , &trigger_width)     ;
  daq->Branch("trigger_channel"   , &trigger_channel)   ;
  daq->Branch("Ch1_status"        , &Ch1_status)  ;
  daq->Branch("Ch2_status"        , &Ch2_status)  ;
  daq->Branch("Ch3_status"        , &Ch3_status)  ;
  daq->Branch("Ch4_status"        , &Ch4_status)  ;
  daq->Branch("temperature"       , &temperature) ;
  daq->Branch("humidity"          , &humidity) ;
  daq->Branch("daqstart"          , daqstart , "daqstart/C");
  daq->Branch("daqend"            , daqend   , "daqend/C"  );
  daq->Branch("memo01"            , memo01   , "memo01/C"  );
  daq->Branch("memo02"            , memo02   , "memo02/C"  );
  daq->Branch("memo03"            , memo03   , "memo03/C"  );
  daq->Branch("memo04"            , memo04   , "memo04/C"  );
  daq->Branch("memo05"            , memo05   , "memo05/C"  );
  daq->Branch("memo06"            , memo06   , "memo06/C"  );
  daq->Branch("memo07"            , memo07   , "memo07/C"  );
  daq->Branch("memo08"            , memo08   , "memo08/C"  );
  daq->Branch("memo09"            , memo09   , "memo09/C"  );
  daq->Branch("memo10"            , memo10   , "memo10/C"  );
  daq->Branch("memo11"            , memo11   , "memo11/C"  );
  daq->Branch("memo12"            , memo12   , "memo12/C"  );
  daq->Branch("memo13"            , memo13   , "memo13/C"  );
  daq->Branch("memo14"            , memo14   , "memo14/C"  );

  xtime->Branch("tu1", &timeUnit1);
  xtime->Branch("tu2", &timeUnit2);
  xtime->Branch("tu3", &timeUnit3);
  xtime->Branch("tu4", &timeUnit4);
  xtime->Branch("t1", t1, "t1[1000]/D");
  xtime->Branch("t2", t2, "t2[1000]/D");
  xtime->Branch("t3", t3, "t3[1000]/D");
  xtime->Branch("t4", t4, "t4[1000]/D");

  wave->Branch("evtid", &evtid);
  wave->Branch("vu1", &voltageUnit1);
  wave->Branch("vu2", &voltageUnit2);
  wave->Branch("vu3", &voltageUnit3);
  wave->Branch("vu4", &voltageUnit4);
  wave->Branch("v1",v1, "v1[1000]/D");
  wave->Branch("v2",v2, "v2[1000]/D");
  wave->Branch("v3",v3, "v3[1000]/D");
  wave->Branch("v4",v4, "v4[1000]/D");

  //------------------------------------------------------------------

}



void lgadTree_SetBranchAddress(TFile *TekFile){

  //
  //   TTree
  //
  daq       = TekFile->Get<TTree>("daq" );
  xtime     = TekFile->Get<TTree>("time");
  wave      = TekFile->Get<TTree>("wave");

  daq->SetBranchAddress("run"               , &runNumber) ;
  daq->SetBranchAddress("RunType"           , &RunType)    ;
  daq->SetBranchAddress("RunFeature"        , &RunFeature) ;
  daq->SetBranchAddress("sensorID"          , sID)   ;
  daq->SetBranchAddress("amp"               , &amp)  ;
  daq->SetBranchAddress("radiation"         , &radiation)  ;
  daq->SetBranchAddress("measurementType"   , &measurementType)  ;
  daq->SetBranchAddress("Vb"                , &biasVoltage)  ;
  daq->SetBranchAddress("source"            , &source)       ;
  daq->SetBranchAddress("trigger_type"      , &trigger_type) ;
  daq->SetBranchAddress("trigger_threshold" , &trigger_threshold) ;
  daq->SetBranchAddress("trigger_width"     , &trigger_width)     ;
  daq->SetBranchAddress("trigger_channel"   , &trigger_channel)   ;
  daq->SetBranchAddress("Ch1_status"        , &Ch1_status)  ;
  daq->SetBranchAddress("Ch2_status"        , &Ch2_status)  ;
  daq->SetBranchAddress("Ch3_status"        , &Ch3_status)  ;
  daq->SetBranchAddress("Ch4_status"        , &Ch4_status)  ;
  daq->SetBranchAddress("temperature"       , &temperature) ;
  daq->SetBranchAddress("humidity"          , &humidity)    ;
  daq->SetBranchAddress("daqstart"          , daqstart) ;
  daq->SetBranchAddress("daqend"            , daqend   );
  daq->SetBranchAddress("memo01"            , memo01   );
  daq->SetBranchAddress("memo02"            , memo02   );
  daq->SetBranchAddress("memo03"            , memo03   );
  daq->SetBranchAddress("memo04"            , memo04   );
  daq->SetBranchAddress("memo05"            , memo05   );
  daq->SetBranchAddress("memo06"            , memo06   );
  daq->SetBranchAddress("memo07"            , memo07   );
  daq->SetBranchAddress("memo08"            , memo08   );
  daq->SetBranchAddress("memo09"            , memo09   );
  daq->SetBranchAddress("memo10"            , memo10   );
  daq->SetBranchAddress("memo11"            , memo11   );
  daq->SetBranchAddress("memo12"            , memo12   );
  daq->SetBranchAddress("memo13"            , memo13   );
  daq->SetBranchAddress("memo14"            , memo14   );

  xtime->SetBranchAddress("tu1",&timeUnit1);
  xtime->SetBranchAddress("tu2",&timeUnit2);
  xtime->SetBranchAddress("tu3",&timeUnit3);
  xtime->SetBranchAddress("tu4",&timeUnit4);
  xtime->SetBranchAddress("t1",t1);
  xtime->SetBranchAddress("t2",t2);
  xtime->SetBranchAddress("t3",t3);
  xtime->SetBranchAddress("t4",t4);

  wave->SetBranchAddress("evtid",&evtid);
  wave->SetBranchAddress("vu1",&voltageUnit1);
  wave->SetBranchAddress("vu2",&voltageUnit2);
  wave->SetBranchAddress("vu3",&voltageUnit3);
  wave->SetBranchAddress("vu4",&voltageUnit4);
  wave->SetBranchAddress("v1",v1);
  wave->SetBranchAddress("v2",v2);
  wave->SetBranchAddress("v3",v3);
  wave->SetBranchAddress("v4",v4);

  //
  //   End of TTree
  //

  //---------------------------------

}


void lgadTree_write() {

  daq->Write();
  xtime->Write();
  wave->Write();

}


























