package repository

import (
	"database/sql"
	"os"
	"path/filepath"
	_ "modernc.org/sqlite" 
)

type DBConnection struct {
	DB *sql.DB
}

func NewDBConnection() (*DBConnection, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return nil, err
	}

	dbPath := filepath.Join(homeDir, ".timetracker.server.db")
	
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		return nil, err
	}

	if err := db.Ping(); err != nil {
		db.Close() // Close the connection if ping fails
		return nil, err
	}

	db.SetMaxOpenConns(10)
	db.SetMaxIdleConns(5)

	return &DBConnection{DB: db}, nil
}

func (d *DBConnection) Close() error {
	return d.DB.Close()
}