-- Social Media Database Schema
USE socialmedia;

-- Users table
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    bio TEXT,
    profile_image_url VARCHAR(255),
    is_verified BOOLEAN DEFAULT FALSE,
    follower_count INT DEFAULT 0,
    following_count INT DEFAULT 0,
    post_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
);

-- Posts table
CREATE TABLE posts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    image_urls JSON,
    hashtags JSON,
    mentions JSON,
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    share_count INT DEFAULT 0,
    is_public BOOLEAN DEFAULT TRUE,
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_is_public (is_public),
    FULLTEXT idx_content (content)
);

-- Comments table
CREATE TABLE comments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    post_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    parent_comment_id BIGINT NULL,
    content TEXT NOT NULL,
    like_count INT DEFAULT 0,
    reply_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_comment_id) REFERENCES comments(id) ON DELETE CASCADE,
    INDEX idx_post_id (post_id),
    INDEX idx_user_id (user_id),
    INDEX idx_parent_comment_id (parent_comment_id),
    INDEX idx_created_at (created_at)
);

-- Likes table
CREATE TABLE likes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    post_id BIGINT NULL,
    comment_id BIGINT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE,
    UNIQUE KEY unique_post_like (user_id, post_id),
    UNIQUE KEY unique_comment_like (user_id, comment_id),
    INDEX idx_user_id (user_id),
    INDEX idx_post_id (post_id),
    INDEX idx_comment_id (comment_id),
    INDEX idx_created_at (created_at),
    CONSTRAINT chk_like_target CHECK (
        (post_id IS NOT NULL AND comment_id IS NULL) OR 
        (post_id IS NULL AND comment_id IS NOT NULL)
    )
);

-- Follows table
CREATE TABLE follows (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    follower_id BIGINT NOT NULL,
    following_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_follow (follower_id, following_id),
    INDEX idx_follower_id (follower_id),
    INDEX idx_following_id (following_id),
    INDEX idx_created_at (created_at),
    CONSTRAINT chk_no_self_follow CHECK (follower_id != following_id)
);

-- Hashtags table for better hashtag management
CREATE TABLE hashtags (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    post_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_post_count (post_count)
);

-- Post hashtags junction table
CREATE TABLE post_hashtags (
    post_id BIGINT NOT NULL,
    hashtag_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (post_id, hashtag_id),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (hashtag_id) REFERENCES hashtags(id) ON DELETE CASCADE,
    INDEX idx_post_id (post_id),
    INDEX idx_hashtag_id (hashtag_id)
);

-- Insert sample data
INSERT INTO users (username, email, full_name, bio, is_verified) VALUES
('john_doe', 'john@example.com', 'John Doe', 'Software developer and tech enthusiast', TRUE),
('jane_smith', 'jane@example.com', 'Jane Smith', 'Digital artist and photographer', FALSE),
('tech_guru', 'guru@example.com', 'Tech Guru', 'Sharing the latest in technology', TRUE),
('foodie_lover', 'foodie@example.com', 'Food Lover', 'Exploring cuisines around the world', FALSE),
('travel_blogger', 'travel@example.com', 'Travel Blogger', 'Documenting adventures worldwide', TRUE);

INSERT INTO hashtags (name) VALUES
('#technology'), ('#programming'), ('#travel'), ('#food'), ('#photography'),
('#art'), ('#nature'), ('#fitness'), ('#music'), ('#books');

INSERT INTO posts (user_id, content, hashtags, is_public) VALUES
(1, 'Just finished building an amazing web application! The future of tech is bright. 🚀', JSON_ARRAY('#technology', '#programming'), TRUE),
(2, 'Captured this beautiful sunset today. Nature never fails to amaze me! 📸', JSON_ARRAY('#photography', '#nature'), TRUE),
(3, 'New AI breakthrough announced today. This will change everything! 🤖', JSON_ARRAY('#technology', '#ai'), TRUE),
(4, 'Tried the most amazing pasta in Italy today. Food is love! 🍝', JSON_ARRAY('#food', '#travel'), TRUE),
(5, 'Exploring the mountains of Nepal. What an incredible journey! 🏔️', JSON_ARRAY('#travel', '#nature'), TRUE);

INSERT INTO comments (post_id, user_id, content) VALUES
(1, 2, 'Congratulations! What technology stack did you use?'),
(1, 3, 'Looks amazing! Would love to see a demo.'),
(2, 1, 'Beautiful shot! What camera did you use?'),
(3, 4, 'This is incredible! The future is here.'),
(4, 5, 'That looks delicious! What restaurant was this?');

INSERT INTO likes (user_id, post_id) VALUES
(2, 1), (3, 1), (4, 1),
(1, 2), (3, 2), (5, 2),
(1, 3), (2, 3), (4, 3), (5, 3),
(1, 4), (2, 4), (3, 4),
(1, 5), (2, 5), (3, 5), (4, 5);

INSERT INTO follows (follower_id, following_id) VALUES
(1, 2), (1, 3), (1, 5),
(2, 1), (2, 4), (2, 5),
(3, 1), (3, 2), (3, 4),
(4, 1), (4, 2), (4, 3), (4, 5),
(5, 1), (5, 2), (5, 3), (5, 4);

-- Update counts based on inserted data
UPDATE users SET 
    follower_count = (SELECT COUNT(*) FROM follows WHERE following_id = users.id),
    following_count = (SELECT COUNT(*) FROM follows WHERE follower_id = users.id),
    post_count = (SELECT COUNT(*) FROM posts WHERE user_id = users.id);

UPDATE posts SET 
    like_count = (SELECT COUNT(*) FROM likes WHERE post_id = posts.id),
    comment_count = (SELECT COUNT(*) FROM comments WHERE post_id = posts.id);

UPDATE comments SET 
    like_count = (SELECT COUNT(*) FROM likes WHERE comment_id = comments.id);