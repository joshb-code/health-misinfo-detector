CREATE TABLE posts (
    post_id SERIAL PRIMARY KEY,
    reddit_id VARCHAR(255) UNIQUE,
    source VARCHAR(255),
    title TEXT NOT NULL,
    body TEXT,
    author_hash VARCHAR(255),
    score FLOAT,
    num_comments INT,
    upvote_ratio FLOAT,
    flair VARCHAR(100),
    post_date TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    searchterm VARCHAR(255)
);

CREATE TABLE comments (
    comment_id SERIAL PRIMARY KEY,
    reddit_comment_id VARCHAR(255) UNIQUE,
    post_id INT,
    content TEXT NOT NULL,
    author_hash VARCHAR(255),
    score FLOAT,
    upvote_ratio FLOAT,
    comment_date TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    searchterm VARCHAR(255),
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
); 

CREATE TABLE labels (
    label_id SERIAL PRIMARY KEY,
    post_id INT,
    comment_id INT,
    label VARCHAR(50) NOT NULL,
    labeled_type VARCHAR(255),
    confidence FLOAT,
    reasoning TEXT,
    labeled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
    FOREIGN KEY (comment_id) REFERENCES comments(comment_id) ON DELETE CASCADE
);

CREATE TABLE predictions (
    prediction_id SERIAL PRIMARY KEY,
    post_id INT,
    comment_id INT,
    predicted_label VARCHAR(50) NOT NULL,
    model_version VARCHAR(255),
    confidence FLOAT,
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
    FOREIGN KEY (comment_id) REFERENCES comments(comment_id) ON DELETE CASCADE
);