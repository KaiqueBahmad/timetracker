package repository

import (
	"database/sql"
	"time"
)

type User struct {
    ID           int64     `json:"id"`
    Username     string    `json:"username"`
    Email        string    `json:"email"`
    PasswordHash string    `json:"-"`
    CreatedAt    time.Time `json:"-"`
}

type UserRepository struct {
	db *sql.DB
}

func NewUserRepository(db *sql.DB) *UserRepository {
	return &UserRepository{db: db}
}

func (r *UserRepository) GetAll() ([]User, error) {
	rows, err := r.db.Query(`
		SELECT id, username, email, password_hash, created_at 
		FROM user
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var users []User
	for rows.Next() {
		var user User
		if err := rows.Scan(
			&user.ID,
			&user.Username,
			&user.Email,
			&user.PasswordHash,
			&user.CreatedAt,
		); err != nil {
			return nil, err
		}
		users = append(users, user)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return users, nil
}

func (r *UserRepository) GetByID(id int64) (User, error) {
	var user User
	row := r.db.QueryRow(`
		SELECT id, username, email, password_hash, created_at 
		FROM user WHERE id = ?
	`, id)
	
	err := row.Scan(
		&user.ID,
		&user.Username,
		&user.Email,
		&user.PasswordHash,
		&user.CreatedAt,
	)
	return user, err
}

func (r *UserRepository) GetByUsername(username string) (User, error) {
	var user User
	row := r.db.QueryRow(`
		SELECT id, username, email, password_hash, created_at 
		FROM user WHERE username = ?
	`, username)
	
	err := row.Scan(
		&user.ID,
		&user.Username,
		&user.Email,
		&user.PasswordHash,
		&user.CreatedAt,
	)
	return user, err
}

func (r *UserRepository) Create(user User) (int64, error) {
	result, err := r.db.Exec(`
		INSERT INTO user (username, email, password_hash) 
		VALUES (?, ?, ?)
	`, user.Username, user.Email, user.PasswordHash)
	
	if err != nil {
		return 0, err
	}
	return result.LastInsertId()
}

func (r *UserRepository) Update(user User) error {
	_, err := r.db.Exec(`
		UPDATE user 
		SET username = ?, email = ?, password_hash = ? 
		WHERE id = ?
	`, user.Username, user.Email, user.PasswordHash, user.ID)
	
	return err
}

func (r *UserRepository) Delete(id int64) error {
	_, err := r.db.Exec("DELETE FROM user WHERE id = ?", id)
	return err
}