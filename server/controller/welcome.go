package controllers

import (
	"github.com/gin-gonic/gin"
)

type WelcomeController struct {
}

func NewWelcomeController() *WelcomeController {
	return &WelcomeController{}
}

func (c *WelcomeController) RegisterRoutes(router *gin.Engine, prefix string) {
	userGroup := router.Group(prefix)
	{
		userGroup.GET("/", c.showSlash)
		userGroup.GET("/welcome", c.welcomeSir)
	}
}

func (cw *WelcomeController) showSlash(c *gin.Context) {
	c.JSON(200, gin.H{
		"message": "Welcome to the main endpoint",
	})
}

func (cw *WelcomeController) welcomeSir(c *gin.Context) {
	c.JSON(200, gin.H{
		"message": "Welcome, Sir!",
	})
}
