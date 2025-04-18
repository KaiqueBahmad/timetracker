package main

import (
	"log"

	"github.com/gin-gonic/gin"
	controllers "github.com/kaiquebahmad/timetracker/server/controller"
	"github.com/kaiquebahmad/timetracker/server/repository"
)

func main() {
	r := gin.Default()
	dbConection, err := repository.NewDBConnection()

	if err != nil {
		log.Fatalf("Falha ao conectar com o banco de dados: %v", err)
	}

	userRepository := repository.NewUserRepository(dbConection.DB)
	userController := controllers.NewUserController(userRepository)

	userController.RegisterRoutes(r, "/users")

	welcomeController := controllers.NewWelcomeController()
	welcomeController.RegisterRoutes(r, "")
	r.Run(":8080")
}
