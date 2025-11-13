#include "lgadTree.h"
#include "BufferRead.h"
#include "RunConfig.h"

//------------------------------------------------------------------------------------

void lgadTree_Fill_daqinfo(){

   Read_RunConfig();
   Read_CurrentRunNumber();
   Read_DaqTimeStart();
   Read_DaqTimeEnd();

   getConfigValue_double ("runNumber"         , runNumber  );
   getConfigValue_char   ("RunType"           , RunType    );
   getConfigValue_char   ("RunFeature"        , RunFeature );
   getConfigValue_char   ("Sensor"            , sID       );
   getConfigValue_double ("Radiation"         , radiation );
   getConfigValue_double ("AMP"               , amp       );     
   getConfigValue_double ("MeasurementType"   , measurementType);  
   getConfigValue_double ("BiasVoltage"       , biasVoltage );  
   getConfigValue_double ("Source"            , source      );        
   getConfigValue_double ("Trigger_Type"      , trigger_type);  
   getConfigValue_double ("Trigger_Threshold" , trigger_threshold );  
   getConfigValue_double ("Trigger_Width"     , trigger_width     );     
   getConfigValue_double ("Trigger_Channel"   , trigger_channel   );   
   getConfigValue_double ("Channel_1_Status"  , Ch1_status );  
   getConfigValue_double ("Channel_2_Status"  , Ch2_status );  
   getConfigValue_double ("Channel_3_Status"  , Ch3_status );  
   getConfigValue_double ("Channel_4_Status"  , Ch4_status );  
   getConfigValue_double ("Temperature"       , temperature );       
   getConfigValue_double ("Humidity"          , humidity  );          
   getConfigValue_char   ("daqstart"          , daqstart  );
   getConfigValue_char   ("daqend"            , daqend );
   getConfigValue_char   ("memo01"            , memo01 );
   getConfigValue_char   ("memo02"            , memo02 );
   getConfigValue_char   ("memo03"            , memo03 );
   getConfigValue_char   ("memo04"            , memo04 );
   getConfigValue_char   ("memo05"            , memo05 );
   getConfigValue_char   ("memo06"            , memo06 );
   getConfigValue_char   ("memo07"            , memo07 );
   getConfigValue_char   ("memo08"            , memo08 );
   getConfigValue_char   ("memo09"            , memo09 );
   getConfigValue_char   ("memo10"            , memo10 );
   getConfigValue_char   ("memo11"            , memo11 );
   getConfigValue_char   ("memo12"            , memo12 );
   getConfigValue_char   ("memo13"            , memo13 );
   getConfigValue_char   ("memo14"            , memo14 );

   daq->Fill();

}



void WaveToTree() {
//-----------------------------------------
//
//  main program  
//
//----------------------------------------
  TString fname;
  ifstream flist;


  // open root file
  //
  TFile *TekFile    = new TFile("tek.root", "RECREATE") ;

  // Init. TTree  ------------------------------------------------------
  //
  lgadTree_wave_Define()  ;
  lgadTree_Fill_daqinfo() ;

  //
  // End of Filling DAQ conditions -------------------------------------



  // Makeing list of data files in Buffer
  // 
  //     How many files ?
  
  int fnumber;
  gSystem->Exec("ls BUFFER/sav/data*.txt  2>/dev/null |wc -l > m");
  flist.open("m"); flist >> fnumber ; flist.close();
  gSystem->Exec("rm m");

  //     Getting file list 

  gSystem->Exec("ls BUFFER/sav/data*.txt > data_file_list 2>/dev/null ");
  flist.open("data_file_list");
  //
  //  making file list is done

  // Loop over files and filling TTree ( time, wave )
  //
  for(int ifile=0;ifile<fnumber;ifile++){ // for 0 

      flist >> fname ;
      // infile.open(fname);
      OpenBufferFile(fname);

      //
      ReadTimeAxis(ifile, timeUnit1, timeUnit2, timeUnit3, timeUnit4, t1, t2, t3, t4 );
      //
      // Filling TTree :  xtime 
      //    Only once is enough.
      //
      if(ifile==0) xtime->Fill(); 


      for(int iev=0;iev<5;iev++){   // for 1.   processing  5 events in the file

         //
         ReadWaveForm(ifile, iev, evtid, voltageUnit1, voltageUnit2, voltageUnit3, voltageUnit4, v1, v2, v3, v4);
         cout << "Event_ID = " << evtid << "  :  Converting to TTree format ..... " << endl;  // print out event id
         //
         // Filling TTree :  wave 
         wave->Fill(); 

      }  // for 1

      CloseBufferFile();
  
  } // for 0 

  flist.close();
  gSystem->Exec("rm data_file_list");

  if(fnumber>0){
     //  Save all TTree to root file
     //
     //
     //  Let's take a break...
     //
     cout << endl ;
     cout << ">>> Daq finished.  Run = " << runNumber << endl;
//     cout << "Wait " ;
//     cout << "." << flush ; gSystem->Sleep(500);
//     cout << "." << flush ; gSystem->Sleep(500);
//     cout << "." << flush ; gSystem->Sleep(500);
//     cout << endl ;
//     cout << endl ;
     //

     daq->Write();
     xtime->Write();
     wave->Write();

  
     // move tek.root to store
     //  
     TString target, rootfile, outdir ;
     TString cmd0, cmd1, cmd2 , cmd3 , cmd4, cmd5;
     int irad, iamp, itype;

     irad = radiation;
     iamp = amp ;
     itype = measurementType;

     target  = "run_";
     target  = target + runNumber     + "_" ;
     target  = target + sID           + "_" ;
     target  = target + tagRad[irad]  + "_" ;
     target  = target + tagAmp[iamp]  + "_" ;
     target  = target + tagTyp[itype] + "_" ;
     target  = target + biasVoltage   + "V" ;
     if ( strcmp(RunFeature, "no" ) != 0 )  target  = target + "_" + RunFeature ; 
 
     rootfile = target + ".root"; 

     outdir   = RunType ;
     outdir   = outdir + "/" + target ;

     cmd0 = "rm BUFFER/data*.txt 2>/dev/null";
     cmd1 = "mv tek.root BUFFER/" + rootfile;
     cmd2 = "cp Tek.run.config BUFFER";
     cmd3 = "mv Tek.run.time.start BUFFER";
     cmd4 = "mv Tek.run.time.end   BUFFER";
     cmd5 = "mv BUFFER " + outdir;

     gSystem->Exec(cmd0);
     gSystem->Exec(cmd1);
     gSystem->Exec(cmd2);
     gSystem->Exec(cmd3);
     gSystem->Exec(cmd4);
     gSystem->Exec(cmd5);


     cout << ">>> All events are saved in " << outdir.Data() << endl;
     cout << ">>> " << target << " Done" << endl << endl;

  } else {
     cout << ">>> There is no data .... I quit. " << endl;
  }

  //  Close root file
  //
  TekFile->Close();
  cout << endl;
  cout << endl;

  // set next run number 
  //

  Set_NextRunNumber();

}
