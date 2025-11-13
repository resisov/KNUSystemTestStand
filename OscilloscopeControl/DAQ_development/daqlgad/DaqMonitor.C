#include "lgadTree.h"
#include "BufferRead.h"
#include "RunConfig.h"

//
//
TCanvas *mon = new TCanvas("mon", "mon", 100, 10, 1000, 1300);


TH2* m1   = new TH2D("m1",   " "         ,  10 , 0, 1 , 10 , 0, 1);
TH2* m2   = new TH2D("m2",   " "         ,  10 , -6, 6 , 10 , -9000, 600);
TH2* w1   = new TH2D("w3",   "Wave_Pulse_ALL"  ,  10 , -6, 6 , 10 , -9000, 600);
TH2* w2   = new TH2D("w4",   "Wave_Noise_ALL"  ,  10 , -6, 6 , 10 , -9000, 600);
TH2* w3   = new TH2D("w1",   "Wave_Pulse"      ,  10 , -6, 6 , 10 , -9000, 600);
TH2* w4   = new TH2D("w2",   "Wave_Noise"      ,  10 , -6, 6 , 10 , -9000, 600);

  
TGraph* gr = new TGraph();             

TPaveText *pt = new TPaveText(-5.5,-8000, -1.5,-5000);
TString strtmp1, strtmp2, strtmp3;

double x[1000],y[1000];
double x_t1[1000], x_t2[1000], x_t3[1000], x_t4[1000];
double y_v1[1000], y_v2[1000], y_v3[1000], y_v4[1000];
double t1_unit, t2_unit, t3_unit, t4_unit;
double v1_unit, v2_unit, v3_unit, v4_unit;

double Npulse, Nnoise, Rpulse, Rnoise;
//
//

void daq_monitor_init(){

     ifstream tekconfig;
     TString  configLINE;
     TString  runTitle;

     Npulse = 0;
     Nnoise = 0;

     mon->Divide(2,3);

     mon->cd(3); w1->Draw();
     mon->cd(4); w2->Draw();
     mon->cd(5); w3->Draw();
     mon->cd(6); w4->Draw();

     //   PAVE_1
     // 
     //   Display Tek.run.config
     // 
     mon->cd(1);


     Read_CurrentRunNumber();
     getConfigValue_double ("runNumber" , runNumber );

     runTitle.Form("Run = %.0f" , runNumber);
     TLatex *lat = new TLatex(0.1, 0.9, runTitle.Data()); 
     lat->SetTextSize(0.1);
     lat->Draw(); 

     TPaveText *memo1 = new TPaveText(0.0, 0.01, 0.99, 0.89);

     tekconfig.open("Tek.run.config");
    
     memo1->AddText("  "); 
     for(int i=0;i<18;i++){
        configLINE.ReadLine(tekconfig); memo1->AddText(configLINE.Data());
     }

     memo1->SetTextAlign(11);
     memo1->Draw(); 


     //   PAVE_2
     // 
     //   Display addtional memos 
     // 

     mon->cd(2);

     TLatex *lat2 = new TLatex(0.0, 0.9, "Additional memos"); 
     lat2->SetTextSize(0.07);
     lat2->Draw(); 

     TPaveText *memo2 = new TPaveText(0.0, 0.01, 0.99, 0.89);

     configLINE.ReadLine(tekconfig); 
     configLINE.ReadLine(tekconfig); 

     memo2->AddText("  "); 
     for(int i=0;i<14;i++){
        configLINE.ReadLine(tekconfig); memo2->AddText(configLINE.Data());
     }

     memo2->SetTextAlign(11);
     memo2->Draw(); 

     tekconfig.close();

}



void MonAnalyser(int ifile, TString datafile){

  bool cut;

  mon->cd(5); w3->Draw();  // pulse in this datafile 
  mon->cd(6); w4->Draw();  // noise in this datafile
 
  OpenBufferFile(datafile);

  //
  ReadTimeAxis(ifile, timeUnit1, timeUnit2, timeUnit3, timeUnit4, t1, x, t3, t4 );
  //

  for(int iev=0;iev<5;iev++){   // for 1.   processing  5 events in the file

      //
      ReadWaveForm(ifile, iev, evtid, voltageUnit1, voltageUnit2, voltageUnit3, voltageUnit4, v1, y, v3, v4);
      //


      gr = new TGraph(1000,x,y);             
        
      cut = 1>0 ;
 
      if  ( cut ) {  // if (1)
         //
         //  OK....  This wave is PULSE
         //

          Npulse = Npulse + 1;

          mon->cd(3); gr->Draw("same"); 
          mon->cd(5); gr->Draw("same"); 

      } else {  // if (1)
          //
          //  OTL ....  This wave is NOISE
          //

          Nnoise = Nnoise + 1;

          mon->cd(4); gr->Draw("same");
          mon->cd(6); gr->Draw("same");
      }  // if (1)

        
      mon->Update();
 

  }  // for 1



  mon->cd(3); 

  Rpulse = 100*Npulse/(Npulse+Nnoise);

  strtmp3.Form("N_Wave = %.0f" , Npulse+Nnoise);
  strtmp1.Form("N_Pulse = %.0f" , Npulse);
  strtmp2.Form("Ratio = %.2f %s" , Rpulse,"%");

  pt->Clear(); 
  pt->AddText(strtmp3); pt->AddText(strtmp1); pt->AddText(strtmp2); pt->Draw(); 


  CloseBufferFile();

}



void daq_monitor_makeplot(int ifile, TString datafile){
// 
//   Analysis and making monitoring plots
//
     cout << datafile << " arrived" << endl;
     MonAnalyser(ifile, datafile);
     //gSystem->Exec("mv "+datafile+" BUFFER/sav");
     gSystem->Exec("rm "+datafile);
}

void DaqMonitor(){


    ifstream control,flist;
    TString fname;
    int DAQ_RUNNING,YES=0,NO=1;
    int fnumber;

    // setup daq canvas
    gStyle->SetOptStat(0);


    // waiting for data
//    while(!control.is_open()){
//        	
//        gSystem->Sleep(500);
//        cout << ">>>> Waiting for data .... " << endl;  
//        control.open("COMMAND_DAQ_START");
//    
//    }
//    control.close();
//    gSystem->Exec("rm COMMAND_DAQ_START");

    // start daq monitoring
    cout << "Daq Monitor starting .... " << endl;
    DAQ_RUNNING=YES;

    daq_monitor_init();

    do{

       cout << "." << flush;
       gSystem->Sleep(500); // 0.5 second 

       // how many files are there ??
       gSystem->Exec("ls BUFFER/data*.txt  2>/dev/null |wc -l > m");
       flist.open("m"); flist >> fnumber ; flist.close();
       gSystem->Exec("rm m");

       // getting file names
       gSystem->Exec("ls BUFFER/data*.txt > mon_file_list 2>/dev/null ");

       flist.open("mon_file_list");
       // 
       // do analysis and updating plots
       //
       for(int ifile=0;ifile<fnumber;ifile++){ 
           if(ifile==0) cout << endl;
           flist >> fname ;

           // checking terminated or not
           control.open("COMMAND_DAQ_TERMINATE");
	   if ( control.is_open() ) 
             fnumber = 0 ;
           else
             daq_monitor_makeplot(ifile,fname);
       }
       flist.close();
       gSystem->Exec("rm mon_file_list");
    
       control.open("COMMAND_MON_PAUSE");
       if ( control.is_open() ) {
          control.close();
          gSystem->Exec("rm COMMAND_MON_PAUSE");
          do{
              control.close();
              control.open("COMMAND_MON_START");
              cout << "Pasue.   excute ./cmd_mon_start to resume" << endl;
              gSystem->Sleep(500);
          } while(!control.is_open());  
          control.close();
          gSystem->Exec("rm COMMAND_MON_START");
       } 
       // checking this daq is stop or not 
       if(fnumber==0) {
          control.open("COMMAND_MON_STOP");
          if ( control.is_open() ) {
	      control.close();
  	      DAQ_RUNNING=NO;  
              gSystem->Exec("rm COMMAND_MON_STOP");
          } else 
	    control.close();
       }

    } while(DAQ_RUNNING==YES) ;

    cout << endl ;
    cout << ">>> Monitor done " << endl;
    cout << endl ;
  

}
