package repository

import (
	"database/sql"
)

type Subject struct {
	ID     int64
	Name   string
	UserID int64
}

type SubjectRepository struct {
	db *sql.DB
}

func NewSubjectRepository(db *sql.DB) *SubjectRepository {
	return &SubjectRepository{db: db}
}

func (r *SubjectRepository) GetAll() ([]Subject, error) {
	rows, err := r.db.Query("SELECT id, name, user_id FROM subject")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var subjects []Subject

	for rows.Next() {
		var subject Subject
		if err := rows.Scan(&subject.ID, &subject.Name, &subject.UserID); err != nil {
			return nil, err
		}
		subjects = append(subjects, subject)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return subjects, nil
}

func (r *SubjectRepository) GetByID(id int64) (Subject, error) {
	var subject Subject
	row := r.db.QueryRow("SELECT id, name, user_id FROM subject WHERE id = ?", id)
	err := row.Scan(&subject.ID, &subject.Name, &subject.UserID)
	return subject, err
}

func (r *SubjectRepository) GetByUserID(userID int64) ([]Subject, error) {
	rows, err := r.db.Query("SELECT id, name, user_id FROM subject WHERE user_id = ?", userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var subjects []Subject

	for rows.Next() {
		var subject Subject
		if err := rows.Scan(&subject.ID, &subject.Name, &subject.UserID); err != nil {
			return nil, err
		}
		subjects = append(subjects, subject)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return subjects, nil
}

func (r *SubjectRepository) Create(name string, userID int64) (int64, error) {
	result, err := r.db.Exec("INSERT INTO subject (name, user_id) VALUES (?, ?)", 
		name, userID)
	if err != nil {
		return 0, err
	}
	return result.LastInsertId()
}

func (r *SubjectRepository) Update(subject Subject) error {
	_, err := r.db.Exec("UPDATE subject SET name = ? WHERE id = ? AND user_id = ?", 
		subject.Name, subject.ID, subject.UserID)
	return err
}

func (r *SubjectRepository) Delete(id int64) error {
	_, err := r.db.Exec("DELETE FROM subject WHERE id = ?", id)
	return err
}

func (r *SubjectRepository) DeleteByUserIDAndName(userID int64, name string) error {
	_, err := r.db.Exec("DELETE FROM subject WHERE user_id = ? AND name = ?", userID, name)
	return err
}