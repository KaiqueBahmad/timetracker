package controllers

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/kaiquebahmad/timetracker/server/repository"
)

// UserController manipula as requisições relacionadas a usuários
type UserController struct {
	UserRepository *repository.UserRepository
}

// NewUserController cria uma nova instância do controller de usuários
func NewUserController(UserRepository *repository.UserRepository) *UserController {
	return &UserController{
		UserRepository: UserRepository,
	}
}

func (c *UserController) RegisterRoutes(router *gin.Engine, prefix string) {
	userGroup := router.Group(prefix)
	{
		userGroup.GET("/", c.GetAllUsers)
		userGroup.GET("/:id", c.GetUserByID)
		userGroup.POST("/", c.CreateUser)
		userGroup.PUT("/:id", c.UpdateUser)
		userGroup.DELETE("/:id", c.DeleteUser)
	}
}

// GetAllUsers retorna a lista de todos os usuários
func (c *UserController) GetAllUsers(ctx *gin.Context) {
	users, err := c.UserRepository.GetAll()
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	ctx.JSON(http.StatusOK, users)
}

// GetUserByID retorna um usuário específico pelo ID
func (c *UserController) GetUserByID(ctx *gin.Context) {
	id, err := strconv.ParseInt(ctx.Param("id"), 10, 64)
	if err != nil {
		ctx.JSON(http.StatusNotFound, gin.H{"error": "ID não numérico"})
		return
	}

	user, err := c.UserRepository.GetByID(id)
	if err != nil {
		ctx.JSON(http.StatusNotFound, gin.H{"error": "Usuário não encontrado"})
		return
	}
	ctx.JSON(http.StatusOK, user)
}

// CreateUser cria um novo usuário
func (c *UserController) CreateUser(ctx *gin.Context) {
	ctx.JSON(http.StatusCreated, "")
}

// UpdateUser atualiza um usuário existente
func (c *UserController) UpdateUser(ctx *gin.Context) {
	ctx.JSON(http.StatusOK, "")
}

// DeleteUser remove um usuário
func (c *UserController) DeleteUser(ctx *gin.Context) {
	id, err := strconv.ParseInt(ctx.Param("id"), 10, 64)
	if err != nil {
		ctx.JSON(http.StatusNotFound, gin.H{"error": "ID não numérico"})
		return
	}

	err = c.UserRepository.Delete(id)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	
	ctx.JSON(http.StatusOK, gin.H{"message": "Usuário removido com sucesso"})
}