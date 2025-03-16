package main

import (
	"fmt"
	"log"
	"github.com/kaiquebahmad/timetracker/server/repository"
	_ "modernc.org/sqlite"
)


func main() {
    // Create DB connection
    dbConn, err := repository.NewDBConnection()
    if err != nil {
        log.Fatal("Failed to connect to database:", err)
    }
    defer dbConn.Close() // Ensure connection is closed when program exits
    
    // Create repositories using the shared connection
    userRepo := repository.NewUserRepository(dbConn.DB)
    // subjectRepo := repository.NewSubjectRepository(dbConn.DB)
	
	users, err := userRepo.GetAll()
	if err != nil{
		log.Fatal("Failed: ", err)
	}

	for index, user := range users {
		fmt.Printf("%d\t%d\t%s\n",index, user.ID, user.Username)
	}
}