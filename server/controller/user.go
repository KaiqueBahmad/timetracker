package controllers

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/kaiquebahmad/timetracker/server/repository"
)

type UserController struct {
	UserRepository *repository.UserRepository
}

func NewUserController(UserRepository *repository.UserRepository) *UserController {
	return &UserController{
		UserRepository: UserRepository,
	}
}

func (c *UserController) RegisterRoutes(router *gin.Engine, prefix string) {
	userGroup := router.Group(prefix)
	{
		userGroup.POST("/", c.CreateUser)
		userGroup.GET("/me", c.GetUserByID)
		userGroup.PUT("/:id", c.UpdateUser)
	}
}

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

func (c *UserController) CreateUser(ctx *gin.Context) {
	var user repository.User
	
	if err := ctx.ShouldBindJSON(&user); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{
			"error": "Dados inválidos: " + err.Error(),
		})
		return
	}
	
	if user.Username == "" || user.Email == "" || user.PasswordHash == "" {
		ctx.JSON(http.StatusBadRequest, gin.H{
			"error": "Username, email e senha são obrigatórios",
		})
		return
	}
	
	id, err := c.UserRepository.Create(user)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{
			"error": "Falha ao criar usuário: " + err.Error(),
		})
		return
	}
	
	createdUser, err := c.UserRepository.GetByID(id)
	if err != nil {
		ctx.JSON(http.StatusCreated, gin.H{
			"id": id,
			"message": "Usuário criado com sucesso",
		})
		return
	}
	
	ctx.JSON(http.StatusCreated, createdUser)
}

func (c *UserController) UpdateUser(ctx *gin.Context) {
	idParam := ctx.Param("id")
	id, err := strconv.ParseInt(idParam, 10, 64)
	if err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{
			"error": "ID inválido",
		})
		return
	}
	
	existingUser, err := c.UserRepository.GetByID(id)
	if err != nil {
		ctx.JSON(http.StatusNotFound, gin.H{
			"error": "Usuário não encontrado",
		})
		return
	}
	
	var updateData repository.User
	if err := ctx.ShouldBindJSON(&updateData); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{
			"error": "Dados inválidos: " + err.Error(),
		})
		return
	}
	
	updateData.ID = id
	
	if updateData.Username == "" {
		updateData.Username = existingUser.Username
	}
	if updateData.Email == "" {
		updateData.Email = existingUser.Email
	}
	if updateData.PasswordHash == "" {
		updateData.PasswordHash = existingUser.PasswordHash
	}
	
	err = c.UserRepository.Update(updateData)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{
			"error": "Falha ao atualizar usuário: " + err.Error(),
		})
		return
	}
	
	updatedUser, err := c.UserRepository.GetByID(id)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{
			"error": "Usuário atualizado, mas falha ao recuperar dados",
		})
		return
	}
	
	ctx.JSON(http.StatusOK, updatedUser)
}
