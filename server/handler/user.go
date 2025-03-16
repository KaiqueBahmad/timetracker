package handlers

import (
	"encoding/json"
	"net/http"
	"time"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"github.com/kaiquebahmad/timetracker/server/repository"
)

type UserHandler struct {
	userRepo *repository.UserRepository
}

func NewUserHandler(userRepo *repository.UserRepository) *UserHandler {
	return &UserHandler{
		userRepo: userRepo,
	}
}

type CreateUserRequest struct {
	Username string `json:"username"`
	Email    string `json:"email"`
	Password string `json:"password"`
}

type CreateUserResponse struct {
	ID       int64  `json:"id"`
	Username string `json:"username"`
	Email    string `json:"email"`
	Created  bool   `json:"created"`
	Message  string `json:"message,omitempty"`
}

// Função para gerar um hash seguro da senha com salt
func hashPassword(password string) (string, error) {
	// Cria um salt aleatório
	salt := make([]byte, 16)
	_, err := rand.Read(salt)
	if err != nil {
		return "", err
	}
	
	// Cria o hash com o salt
	hash := sha256.New()
	_, err = hash.Write([]byte(password))
	if err != nil {
		return "", err
	}
	_, err = hash.Write(salt)
	if err != nil {
		return "", err
	}
	
	// Combina o salt + hash em uma única string para armazenar
	hashedPassword := hex.EncodeToString(salt) + ":" + hex.EncodeToString(hash.Sum(nil))
	return hashedPassword, nil
}

// Handler para criar um novo usuário
func (h *UserHandler) CreateUser(w http.ResponseWriter, r *http.Request) {
	// Verifica se o método é POST
	if r.Method != http.MethodPost {
		http.Error(w, "Método não permitido", http.StatusMethodNotAllowed)
		return
	}

	// Lê o corpo da requisição
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Erro ao ler requisição", http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	// Decodifica o JSON
	var request CreateUserRequest
	if err := json.Unmarshal(body, &request); err != nil {
		http.Error(w, "JSON inválido", http.StatusBadRequest)
		return
	}

	// Validação básica
	if request.Username == "" || request.Email == "" || request.Password == "" {
		response := CreateUserResponse{
			Created: false,
			Message: "Username, email e senha são obrigatórios",
		}
		
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(response)
		return
	}

	// Gera o hash da senha
	hashedPassword, err := hashPassword(request.Password)
	if err != nil {
		http.Error(w, "Erro ao processar a senha", http.StatusInternalServerError)
		return
	}

	// Cria o usuário no banco de dados
	user := repository.User{
		Username:     request.Username,
		Email:        request.Email,
		PasswordHash: hashedPassword,
		CreatedAt:    time.Now(),
	}

	id, err := h.userRepo.Create(user)
	if err != nil {
		// Verifica se é um erro de usuário duplicado
		if err.Error() == "UNIQUE constraint failed: user.username" || 
		   err.Error() == "UNIQUE constraint failed: user.email" {
			response := CreateUserResponse{
				Created: false,
				Message: "Username ou email já existe",
			}
			
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusConflict)
			json.NewEncoder(w).Encode(response)
			return
		}
		
		// Outro erro
		http.Error(w, fmt.Sprintf("Erro ao criar usuário: %v", err), http.StatusInternalServerError)
		return
	}

	// Prepara a resposta
	response := CreateUserResponse{
		ID:       id,
		Username: request.Username,
		Email:    request.Email,
		Created:  true,
		Message:  "Usuário criado com sucesso",
	}

	// Envia a resposta
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(response)
}