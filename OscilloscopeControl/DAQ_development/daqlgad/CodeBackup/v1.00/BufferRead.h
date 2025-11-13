TObjArray *_tx ;
ifstream _infile;


void OpenBufferFile(TString fname){
     _infile.open(fname);
}

void CloseBufferFile(){
     _infile.close();
}

void readChannelUnit(TString tmpSTRING, double &axisUnit){
   _tx = tmpSTRING.Tokenize(" ");
   axisUnit =  (((TObjString *)(_tx->At(1)))->String()).Atof() ;
}


void readChannelArray(TString tmpSTRING, double arr[]){
  _tx = tmpSTRING.Tokenize(" ");
  for(int i=0;i<_tx->GetEntries();i++){
     arr[i] =  (((TObjString *)(_tx->At(i)))->String()).Atof() ;
  }
}



void ReadTimeAxis(int fileId,
                  double &u1, double &u2, double &u3, double &u4,
                  double a1[], double a2[], double a3[], double a4[]){

     TString STRING;

     // time header
     // #time
     //
     STRING.ReadLine(_infile); // #time

     // time of channel 1
     //
     STRING.ReadLine(_infile); if(fileId==0) readChannelUnit(  STRING, u1);
     STRING.ReadLine(_infile); if(fileId==0) readChannelArray( STRING, a1);

     // time of channel 2
     //
     STRING.ReadLine(_infile); if(fileId==0) readChannelUnit(  STRING, u2);
     STRING.ReadLine(_infile); if(fileId==0) readChannelArray( STRING, a2);

     // time of channel 3
     //
     STRING.ReadLine(_infile); if(fileId==0) readChannelUnit(  STRING, u3);
     STRING.ReadLine(_infile); if(fileId==0) readChannelArray( STRING, a3);

     // time of channel 4
     //
     STRING.ReadLine(_infile); if(fileId==0) readChannelUnit(  STRING, u4);
     STRING.ReadLine(_infile); if(fileId==0) readChannelArray( STRING, a4);

}


void ReadWaveForm(int fileId, int iev,
                  double &evid, double &u1, double &u2, double &u3, double &u4,
                  double a1[], double a2[], double a3[], double a4[]){

     TString STRING;
     // wave header
     // #waveform
     //
     if (iev==0) STRING.ReadLine(_infile); // #wave


     // event id
     // ....
     STRING.ReadLine(_infile); readChannelUnit(STRING, evid);  // event id

     // voltage of channel 1
     //
     STRING.ReadLine(_infile); readChannelUnit(  STRING, u1);
     STRING.ReadLine(_infile); readChannelArray( STRING, a1);

     // voltage of channel 2
     //
     STRING.ReadLine(_infile); readChannelUnit(  STRING, u2);
     STRING.ReadLine(_infile); readChannelArray( STRING, a2);

     // voltage of channel 3
     //
     STRING.ReadLine(_infile); readChannelUnit(  STRING, u3);
     STRING.ReadLine(_infile); readChannelArray( STRING, a3);

     // voltage of channel 4
     //
     STRING.ReadLine(_infile); readChannelUnit(  STRING, u4);
     STRING.ReadLine(_infile); readChannelArray( STRING, a4);

}



























