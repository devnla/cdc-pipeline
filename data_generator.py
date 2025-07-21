#!/usr/bin/env python3
"""
Social Media Data Generator

Generates realistic social media data to test the CDC pipeline.
This script continuously creates posts, comments, likes, and follows
to simulate real-time social media activity.
"""

import mysql.connector
import json
import random
import time
from datetime import datetime, timedelta
from faker import Faker
import argparse
import sys
from typing import List, Dict, Any

# Initialize Faker
fake = Faker()

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'dbuser',
    'password': 'dbpassword',
    'database': 'socialmedia',
    'autocommit': True
}

# Sample hashtags for realistic posts
HASHTAGS = [
    '#technology', '#programming', '#ai', '#machinelearning', '#datascience',
    '#webdev', '#mobile', '#cloud', '#devops', '#cybersecurity',
    '#travel', '#photography', '#nature', '#adventure', '#wanderlust',
    '#food', '#cooking', '#recipe', '#restaurant', '#foodie',
    '#fitness', '#health', '#workout', '#yoga', '#running',
    '#music', '#art', '#design', '#creativity', '#inspiration',
    '#business', '#startup', '#entrepreneur', '#innovation', '#leadership',
    '#education', '#learning', '#books', '#knowledge', '#growth',
    '#lifestyle', '#motivation', '#success', '#mindfulness', '#wellness',
    '#sports', '#football', '#basketball', '#soccer', '#tennis'
]

# Sample post templates
POST_TEMPLATES = [
    "Just finished working on {topic}! Feeling {emotion} about the progress. {hashtags}",
    "Amazing {adjective} experience with {topic} today! {hashtags}",
    "Thoughts on {topic}: {opinion}. What do you think? {hashtags}",
    "Can't believe how {adjective} {topic} has become! {hashtags}",
    "Learning about {topic} and it's {emotion}! {hashtags}",
    "Quick tip about {topic}: {tip}. Hope this helps! {hashtags}",
    "Just discovered {topic} and I'm {emotion}! {hashtags}",
    "Working on {topic} project. {progress_update}. {hashtags}",
    "Beautiful {time_of_day} for {activity}! {hashtags}",
    "Excited to share my latest {topic} creation! {hashtags}"
]

# Sample comment templates
COMMENT_TEMPLATES = [
    "Great post! Thanks for sharing.",
    "This is really helpful, thank you!",
    "I completely agree with this.",
    "Interesting perspective!",
    "Love this! Keep up the great work.",
    "Thanks for the inspiration!",
    "This made my day!",
    "Couldn't agree more!",
    "Awesome content as always.",
    "This is exactly what I needed to hear.",
    "So true! Thanks for posting.",
    "Amazing work!",
    "This is gold! 🔥",
    "Bookmarking this for later.",
    "Mind blown! 🤯"
]

class SocialMediaDataGenerator:
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        self.users = []
        self.posts = []
        
    def connect(self):
        """Connect to MySQL database"""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor(dictionary=True)
            print("✅ Connected to MySQL database")
        except mysql.connector.Error as e:
            print(f"❌ Error connecting to MySQL: {e}")
            sys.exit(1)
    
    def disconnect(self):
        """Disconnect from MySQL database"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("🔌 Disconnected from MySQL database")
    
    def load_existing_data(self):
        """Load existing users and posts for realistic interactions"""
        # Load users
        self.cursor.execute("SELECT id, username, full_name FROM users ORDER BY id")
        self.users = self.cursor.fetchall()
        
        # Load recent posts
        self.cursor.execute("""
            SELECT id, user_id, content 
            FROM posts 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            ORDER BY created_at DESC 
            LIMIT 100
        """)
        self.posts = self.cursor.fetchall()
        
        print(f"📊 Loaded {len(self.users)} users and {len(self.posts)} recent posts")
    
    def generate_user(self) -> Dict[str, Any]:
        """Generate a new user"""
        username = fake.user_name() + str(random.randint(100, 999))
        email = fake.email()
        full_name = fake.name()
        bio = fake.text(max_nb_chars=200) if random.random() < 0.7 else None
        is_verified = random.random() < 0.1  # 10% chance of being verified
        
        return {
            'username': username,
            'email': email,
            'full_name': full_name,
            'bio': bio,
            'is_verified': is_verified
        }
    
    def generate_post_content(self) -> tuple:
        """Generate realistic post content with hashtags"""
        template = random.choice(POST_TEMPLATES)
        
        # Generate content variables
        topics = ['AI', 'blockchain', 'cloud computing', 'mobile development', 
                 'data science', 'cybersecurity', 'travel', 'photography',
                 'cooking', 'fitness', 'music', 'art', 'business']
        
        emotions = ['excited', 'amazed', 'inspired', 'motivated', 'thrilled', 'grateful']
        adjectives = ['incredible', 'amazing', 'fantastic', 'awesome', 'brilliant', 'outstanding']
        opinions = ['It\'s game-changing', 'The future is bright', 'Innovation at its best',
                   'This will revolutionize everything', 'Absolutely mind-blowing']
        tips = ['Always test your code', 'Practice makes perfect', 'Stay curious and keep learning',
               'Collaboration is key', 'Don\'t be afraid to fail']
        activities = ['coding', 'learning', 'exploring', 'creating', 'innovating']
        times = ['morning', 'afternoon', 'evening']
        updates = ['Making great progress', 'Almost done', 'Learned so much', 'Challenges overcome']
        
        # Select random hashtags
        selected_hashtags = random.sample(HASHTAGS, random.randint(1, 4))
        hashtags_str = ' '.join(selected_hashtags)
        
        # Fill template
        content = template.format(
            topic=random.choice(topics),
            emotion=random.choice(emotions),
            adjective=random.choice(adjectives),
            opinion=random.choice(opinions),
            tip=random.choice(tips),
            activity=random.choice(activities),
            time_of_day=random.choice(times),
            progress_update=random.choice(updates),
            hashtags=hashtags_str
        )
        
        return content, selected_hashtags
    
    def create_user(self) -> int:
        """Create a new user and return user ID"""
        user_data = self.generate_user()
        
        query = """
            INSERT INTO users (username, email, full_name, bio, is_verified)
            VALUES (%(username)s, %(email)s, %(full_name)s, %(bio)s, %(is_verified)s)
        """
        
        try:
            self.cursor.execute(query, user_data)
            user_id = self.cursor.lastrowid
            
            # Add to local cache
            self.users.append({
                'id': user_id,
                'username': user_data['username'],
                'full_name': user_data['full_name']
            })
            
            print(f"👤 Created user: {user_data['username']} (ID: {user_id})")
            return user_id
            
        except mysql.connector.Error as e:
            print(f"❌ Error creating user: {e}")
            return None
    
    def create_post(self, user_id: int = None) -> int:
        """Create a new post and return post ID"""
        if not user_id and self.users:
            user_id = random.choice(self.users)['id']
        elif not user_id:
            print("❌ No users available for posting")
            return None
        
        content, hashtags = self.generate_post_content()
        
        # Add some mentions occasionally
        mentions = []
        if random.random() < 0.3 and len(self.users) > 1:  # 30% chance of mentions
            mentioned_users = random.sample(
                [u for u in self.users if u['id'] != user_id], 
                min(2, len(self.users) - 1)
            )
            mentions = [f"@{u['username']}" for u in mentioned_users]
            if mentions:
                content += f" {' '.join(mentions)}"
        
        post_data = {
            'user_id': user_id,
            'content': content,
            'hashtags': json.dumps(hashtags),
            'mentions': json.dumps(mentions) if mentions else None,
            'is_public': random.random() < 0.9,  # 90% public posts
            'location': fake.city() if random.random() < 0.3 else None
        }
        
        query = """
            INSERT INTO posts (user_id, content, hashtags, mentions, is_public, location)
            VALUES (%(user_id)s, %(content)s, %(hashtags)s, %(mentions)s, %(is_public)s, %(location)s)
        """
        
        try:
            self.cursor.execute(query, post_data)
            post_id = self.cursor.lastrowid
            
            # Add to local cache
            self.posts.append({
                'id': post_id,
                'user_id': user_id,
                'content': content
            })
            
            # Keep only recent posts in cache
            if len(self.posts) > 100:
                self.posts = self.posts[-100:]
            
            print(f"📝 Created post: {content[:50]}... (ID: {post_id})")
            return post_id
            
        except mysql.connector.Error as e:
            print(f"❌ Error creating post: {e}")
            return None
    
    def create_comment(self, post_id: int = None, user_id: int = None) -> int:
        """Create a new comment and return comment ID"""
        if not post_id and self.posts:
            post_id = random.choice(self.posts)['id']
        elif not post_id:
            print("❌ No posts available for commenting")
            return None
        
        if not user_id and self.users:
            user_id = random.choice(self.users)['id']
        elif not user_id:
            print("❌ No users available for commenting")
            return None
        
        content = random.choice(COMMENT_TEMPLATES)
        
        # Add emoji occasionally
        if random.random() < 0.3:
            emojis = ['😊', '👍', '🔥', '💯', '🚀', '❤️', '👏', '🎉']
            content += f" {random.choice(emojis)}"
        
        comment_data = {
            'post_id': post_id,
            'user_id': user_id,
            'content': content
        }
        
        query = """
            INSERT INTO comments (post_id, user_id, content)
            VALUES (%(post_id)s, %(user_id)s, %(content)s)
        """
        
        try:
            self.cursor.execute(query, comment_data)
            comment_id = self.cursor.lastrowid
            
            print(f"💬 Created comment: {content} (ID: {comment_id})")
            return comment_id
            
        except mysql.connector.Error as e:
            print(f"❌ Error creating comment: {e}")
            return None
    
    def create_like(self, post_id: int = None, user_id: int = None):
        """Create a new like"""
        if not post_id and self.posts:
            post_id = random.choice(self.posts)['id']
        elif not post_id:
            return
        
        if not user_id and self.users:
            user_id = random.choice(self.users)['id']
        elif not user_id:
            return
        
        like_data = {
            'user_id': user_id,
            'post_id': post_id
        }
        
        query = """
            INSERT IGNORE INTO likes (user_id, post_id)
            VALUES (%(user_id)s, %(post_id)s)
        """
        
        try:
            self.cursor.execute(query, like_data)
            if self.cursor.rowcount > 0:
                print(f"❤️ Created like: User {user_id} liked Post {post_id}")
            
        except mysql.connector.Error as e:
            if "Duplicate entry" not in str(e):
                print(f"❌ Error creating like: {e}")
    
    def create_follow(self, follower_id: int = None, following_id: int = None):
        """Create a new follow relationship"""
        if len(self.users) < 2:
            return
        
        if not follower_id:
            follower_id = random.choice(self.users)['id']
        
        if not following_id:
            # Ensure different users
            available_users = [u for u in self.users if u['id'] != follower_id]
            if not available_users:
                return
            following_id = random.choice(available_users)['id']
        
        follow_data = {
            'follower_id': follower_id,
            'following_id': following_id
        }
        
        query = """
            INSERT IGNORE INTO follows (follower_id, following_id)
            VALUES (%(follower_id)s, %(following_id)s)
        """
        
        try:
            self.cursor.execute(query, follow_data)
            if self.cursor.rowcount > 0:
                print(f"👥 Created follow: User {follower_id} follows User {following_id}")
            
        except mysql.connector.Error as e:
            if "Duplicate entry" not in str(e):
                print(f"❌ Error creating follow: {e}")
    
    def generate_activity_burst(self, duration_seconds: int = 60):
        """Generate a burst of social media activity"""
        print(f"🚀 Starting activity burst for {duration_seconds} seconds...")
        
        start_time = time.time()
        activity_count = 0
        
        while time.time() - start_time < duration_seconds:
            # Weighted random activity selection
            activity_weights = {
                'post': 0.3,
                'comment': 0.25,
                'like': 0.35,
                'follow': 0.05,
                'user': 0.05
            }
            
            activity = random.choices(
                list(activity_weights.keys()),
                weights=list(activity_weights.values())
            )[0]
            
            if activity == 'post':
                self.create_post()
            elif activity == 'comment':
                self.create_comment()
            elif activity == 'like':
                self.create_like()
            elif activity == 'follow':
                self.create_follow()
            elif activity == 'user':
                self.create_user()
            
            activity_count += 1
            
            # Random delay between activities
            time.sleep(random.uniform(0.5, 3.0))
        
        print(f"✅ Activity burst completed! Generated {activity_count} activities")
    
    def run_continuous(self, interval_seconds: int = 5):
        """Run continuous data generation"""
        print(f"🔄 Starting continuous data generation (interval: {interval_seconds}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                # Generate random activity
                activities = ['post', 'comment', 'like', 'follow']
                weights = [0.4, 0.3, 0.25, 0.05]
                
                activity = random.choices(activities, weights=weights)[0]
                
                if activity == 'post':
                    self.create_post()
                elif activity == 'comment':
                    self.create_comment()
                elif activity == 'like':
                    self.create_like()
                elif activity == 'follow':
                    self.create_follow()
                
                # Occasionally create new users
                if random.random() < 0.02:  # 2% chance
                    self.create_user()
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping continuous data generation")

def main():
    parser = argparse.ArgumentParser(description='Social Media Data Generator')
    parser.add_argument('--mode', choices=['burst', 'continuous', 'single'], 
                       default='burst', help='Generation mode')
    parser.add_argument('--duration', type=int, default=60, 
                       help='Duration for burst mode (seconds)')
    parser.add_argument('--interval', type=int, default=5, 
                       help='Interval for continuous mode (seconds)')
    parser.add_argument('--activity', choices=['post', 'comment', 'like', 'follow', 'user'],
                       help='Single activity type for single mode')
    
    args = parser.parse_args()
    
    generator = SocialMediaDataGenerator(DB_CONFIG)
    
    try:
        generator.connect()
        generator.load_existing_data()
        
        if args.mode == 'burst':
            generator.generate_activity_burst(args.duration)
        elif args.mode == 'continuous':
            generator.run_continuous(args.interval)
        elif args.mode == 'single':
            if args.activity == 'post':
                generator.create_post()
            elif args.activity == 'comment':
                generator.create_comment()
            elif args.activity == 'like':
                generator.create_like()
            elif args.activity == 'follow':
                generator.create_follow()
            elif args.activity == 'user':
                generator.create_user()
            else:
                print("Please specify --activity for single mode")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        generator.disconnect()

if __name__ == "__main__":
    main()