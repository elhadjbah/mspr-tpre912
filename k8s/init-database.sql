-- Initialisation de la base de données ecommerce
-- Création de la table users

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    mfa VARCHAR(255) NOT NULL,
    gendate TIMESTAMP NOT NULL,
    expired BOOLEAN NOT NULL DEFAULT FALSE
);

-- Insertion de l'utilisateur admin par défaut
INSERT INTO users (username, password, mfa, gendate, expired)
VALUES ('admin', 'admin_pass', 'off', NOW(), false)
ON CONFLICT (username) DO NOTHING;

-- Vérification de la création
SELECT 'Table users créée avec succès!' as message;
SELECT COUNT(*) as nombre_utilisateurs FROM users; 