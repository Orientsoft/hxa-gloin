db.createUser(
  {
    user  : "chromo",
    pwd   : "d2VsY29tZTEK",
    roles : [
      {
        role : "readWrite",
        db   : "chromoManager"
      }	
    ]
  }
)
