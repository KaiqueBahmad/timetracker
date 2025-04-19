package main

import (
	"log"

	"github.com/gin-gonic/gin"
	controllers "github.com/kaiquebahmad/timetracker/server/controller"
	_ "github.com/kaiquebahmad/timetracker/server/docs"
	"github.com/kaiquebahmad/timetracker/server/repository"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
)

// @title Time monitoring API
// @version 1.1

// @host localhost:8080
// @BasePath /
// @description Api for providing facility for tracking your time and exporting this data
func main() {
	r := gin.Default()
	dbConection, err := repository.NewDBConnection()

	if err != nil {
		log.Fatalf("Falha ao conectar com o banco de dados: %v", err)
	}

	r.GET("/docs/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

	userRepository := repository.NewUserRepository(dbConection.DB)
	userController := controllers.NewUserController(userRepository)

	userController.RegisterRoutes(r, "/users")

	welcomeController := controllers.NewWelcomeController()
	welcomeController.RegisterRoutes(r, "")
	r.Run(":8080")
}
