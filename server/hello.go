package main

import (
	"fmt"
	"log"
	"net/http"
	"github.com/kaiquebahmad/timetracker/server/repository"
	"github.com/kaiquebahmad/timetracker/server/handler"
	_ "modernc.org/sqlite"
)


func main() {
	// Inicializa a conexão com o banco de dados
	dbConn, err := repository.NewDBConnection()
	if err != nil {
		log.Fatal("Falha ao conectar ao banco de dados:", err)
	}
	defer dbConn.Close()

	userRepo := repository.NewUserRepository(dbConn.DB)
	
	userHandler := handlers.NewUserHandler(userRepo)

	http.HandleFunc("/api/users", userHandler.CreateUser)

	port := 8080
	fmt.Printf("Servidor iniciado na porta %d...\n", port)
	err = http.ListenAndServe(fmt.Sprintf(":%d", port), nil)
	if err != nil {
		log.Fatal("Erro ao iniciar o servidor:", err)
	}
}