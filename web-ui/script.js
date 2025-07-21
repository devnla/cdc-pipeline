// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Global state
let currentTab = 'all';
let currentQuery = '';
let searchTimeout = null;

// DOM Elements
const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearch');
const searchSuggestions = document.getElementById('searchSuggestions');
const loadingSpinner = document.getElementById('loadingSpinner');
const welcomeMessage = document.getElementById('welcomeMessage');
const resultsContainer = document.getElementById('resultsContainer');
const resultsTitle = document.getElementById('resultsTitle');
const resultsCount = document.getElementById('resultsCount');
const resultsContent = document.getElementById('resultsContent');
const noResults = document.getElementById('noResults');
const postModal = document.getElementById('postModal');
const modalBody = document.getElementById('modalBody');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    loadTrendingHashtags();
});

// Event Listeners
function initializeEventListeners() {
    // Search input events
    searchInput.addEventListener('input', handleSearchInput);
    searchInput.addEventListener('keypress', handleSearchKeypress);
    searchInput.addEventListener('focus', showSearchSuggestions);
    searchInput.addEventListener('blur', hideSearchSuggestions);
    
    // Clear search button
    clearSearchBtn.addEventListener('click', clearSearch);
    
    // Tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', handleTabClick);
    });
    
    // Trending hashtags
    document.querySelectorAll('.hashtag-tag').forEach(tag => {
        tag.addEventListener('click', handleHashtagClick);
    });
    
    // Modal close
    document.querySelector('.modal-close').addEventListener('click', closeModal);
    postModal.addEventListener('click', function(e) {
        if (e.target === postModal) {
            closeModal();
        }
    });
    
    // Escape key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

// Search functionality
function handleSearchInput(e) {
    const query = e.target.value.trim();
    
    // Show/hide clear button
    clearSearchBtn.style.display = query ? 'block' : 'none';
    
    // Debounce search
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        if (query) {
            performSearch(query);
        } else {
            showWelcomeMessage();
        }
    }, 300);
}

function handleSearchKeypress(e) {
    if (e.key === 'Enter') {
        const query = e.target.value.trim();
        if (query) {
            performSearch(query);
        }
    }
}

function clearSearch() {
    searchInput.value = '';
    clearSearchBtn.style.display = 'none';
    currentQuery = '';
    showWelcomeMessage();
    searchInput.focus();
}

function showSearchSuggestions() {
    // Implementation for search suggestions can be added here
    // For now, we'll keep it simple
}

function hideSearchSuggestions() {
    setTimeout(() => {
        searchSuggestions.style.display = 'none';
    }, 200);
}

// Tab functionality
function handleTabClick(e) {
    const tabBtn = e.currentTarget;
    const tabName = tabBtn.dataset.tab;
    
    // Update active tab
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    tabBtn.classList.add('active');
    
    currentTab = tabName;
    
    // Perform search with current query if exists
    if (currentQuery) {
        performSearch(currentQuery);
    }
}

// Hashtag functionality
function handleHashtagClick(e) {
    const hashtag = e.target.dataset.hashtag || e.target.textContent;
    const cleanHashtag = hashtag.replace('#', '');
    
    searchInput.value = `#${cleanHashtag}`;
    clearSearchBtn.style.display = 'block';
    performSearch(`#${cleanHashtag}`);
}

// Search API calls
async function performSearch(query) {
    currentQuery = query;
    showLoading();
    
    try {
        let results = [];
        
        switch (currentTab) {
            case 'posts':
                results = await searchPosts(query);
                break;
            case 'users':
                results = await searchUsers(query);
                break;
            case 'hashtags':
                results = await searchHashtags(query);
                break;
            case 'all':
            default:
                results = await searchAll(query);
                break;
        }
        
        displayResults(results, query);
    } catch (error) {
        console.error('Search error:', error);
        showError('Failed to perform search. Please try again.');
    }
}

async function searchPosts(query) {
    const response = await fetch(`${API_BASE_URL}/search/posts?q=${encodeURIComponent(query)}&size=20`);
    if (!response.ok) throw new Error('Failed to search posts');
    return await response.json();
}

async function searchUsers(query) {
    const response = await fetch(`${API_BASE_URL}/search/users?q=${encodeURIComponent(query)}&size=20`);
    if (!response.ok) throw new Error('Failed to search users');
    return await response.json();
}

async function searchHashtags(query) {
    const cleanQuery = query.replace('#', '');
    const response = await fetch(`${API_BASE_URL}/search/hashtags?q=${encodeURIComponent(cleanQuery)}&limit=20`);
    if (!response.ok) throw new Error('Failed to search hashtags');
    return await response.json();
}

async function searchAll(query) {
    try {
        const [postsResponse, usersResponse] = await Promise.all([
            searchPosts(query),
            searchUsers(query)
        ]);
        
        return {
            posts: postsResponse,
            users: usersResponse,
            total: postsResponse.total + usersResponse.total
        };
    } catch (error) {
        console.error('Error in searchAll:', error);
        return { posts: { results: [], total: 0 }, users: { results: [], total: 0 }, total: 0 };
    }
}

// Display functions
function showLoading() {
    hideAllSections();
    loadingSpinner.style.display = 'flex';
}

function showWelcomeMessage() {
    hideAllSections();
    welcomeMessage.style.display = 'block';
}

function showError(message) {
    hideAllSections();
    noResults.style.display = 'block';
    noResults.querySelector('h3').textContent = 'Error';
    noResults.querySelector('p').textContent = message;
}

function hideAllSections() {
    loadingSpinner.style.display = 'none';
    welcomeMessage.style.display = 'none';
    resultsContainer.style.display = 'none';
    noResults.style.display = 'none';
}

function displayResults(results, query) {
    hideAllSections();
    
    if (currentTab === 'all') {
        if (results.total === 0) {
            showNoResults();
            return;
        }
        displayAllResults(results, query);
    } else if (currentTab === 'hashtags') {
        if (!results.hashtags || results.hashtags.length === 0) {
            showNoResults();
            return;
        }
        displayHashtagResults(results, query);
    } else {
        if (!results.results || results.results.length === 0) {
            showNoResults();
            return;
        }
        displayTabResults(results, query);
    }
}

function displayAllResults(results, query) {
    resultsContainer.style.display = 'block';
    resultsTitle.textContent = `Search Results for "${query}"`;
    resultsCount.textContent = `${results.total} results found`;
    
    let html = '';
    
    // Display posts
    if (results.posts.results.length > 0) {
        html += '<h4 style="margin: 2rem 0 1rem 0; color: #1c1e21; font-size: 1.2rem;">Posts</h4>';
        results.posts.results.forEach(post => {
            html += createPostCard(post);
        });
    }
    
    // Display users
    if (results.users.results.length > 0) {
        html += '<h4 style="margin: 2rem 0 1rem 0; color: #1c1e21; font-size: 1.2rem;">Users</h4>';
        results.users.results.forEach(user => {
            html += createUserCard(user);
        });
    }
    
    resultsContent.innerHTML = html;
    attachEventListeners();
}

function displayTabResults(results, query) {
    resultsContainer.style.display = 'block';
    resultsTitle.textContent = `${currentTab.charAt(0).toUpperCase() + currentTab.slice(1)} Results for "${query}"`;
    resultsCount.textContent = `${results.total} results found`;
    
    let html = '';
    
    if (currentTab === 'posts') {
        results.results.forEach(post => {
            html += createPostCard(post);
        });
    } else if (currentTab === 'users') {
        results.results.forEach(user => {
            html += createUserCard(user);
        });
    }
    
    resultsContent.innerHTML = html;
    attachEventListeners();
}

function displayHashtagResults(results, query) {
    resultsContainer.style.display = 'block';
    resultsTitle.textContent = `Hashtag Results for "${query}"`;
    resultsCount.textContent = `${results.hashtags.length} hashtags found`;
    
    let html = '';
    results.hashtags.forEach(hashtag => {
        html += createHashtagCard(hashtag);
    });
    
    resultsContent.innerHTML = html;
    attachEventListeners();
}

function showNoResults() {
    hideAllSections();
    noResults.style.display = 'block';
    noResults.querySelector('h3').textContent = 'No results found';
    noResults.querySelector('p').textContent = 'Try adjusting your search terms or browse trending hashtags.';
}

// Card creation functions
function createPostCard(post) {
    const userInitial = post.user ? post.user.full_name.charAt(0).toUpperCase() : 'U';
    const userName = post.user ? post.user.full_name : 'Unknown User';
    const userHandle = post.user ? `@${post.user.username}` : '@unknown';
    const postDate = new Date(post.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    const hashtags = post.hashtags ? post.hashtags.map(tag => 
        `<span class="hashtag" onclick="searchHashtag('${tag}')">${tag}</span>`
    ).join('') : '';
    
    const location = post.location ? 
        `<div class="post-location"><i class="fas fa-map-marker-alt"></i> ${post.location}</div>` : '';
    
    return `
        <div class="post-card" data-post-id="${post.id}">
            <div class="post-header">
                <div class="user-avatar">${userInitial}</div>
                <div class="user-info">
                    <div class="user-name">${userName} ${post.user && post.user.is_verified ? '<i class="fas fa-check-circle user-verified"></i>' : ''}</div>
                    <div class="post-date">${userHandle} • ${postDate}</div>
                </div>
            </div>
            <div class="post-content">
                <div class="post-text">${post.content}</div>
                ${hashtags ? `<div class="post-hashtags">${hashtags}</div>` : ''}
                ${location}
            </div>
            <div class="post-actions">
                <div class="action-stats">
                    <div class="stat-item">
                        <i class="fas fa-heart"></i>
                        <span>${post.like_count || 0}</span>
                    </div>
                    <div class="stat-item">
                        <i class="fas fa-comment"></i>
                        <span>${post.comment_count || 0}</span>
                    </div>
                    <div class="stat-item">
                        <i class="fas fa-share"></i>
                        <span>${post.share_count || 0}</span>
                    </div>
                </div>
                <div class="action-buttons">
                    <button class="action-btn" onclick="toggleLike(${post.id})">
                        <i class="fas fa-heart"></i>
                        <span>Like</span>
                    </button>
                    <button class="action-btn" onclick="showPostDetails(${post.id})">
                        <i class="fas fa-comment"></i>
                        <span>Comment</span>
                    </button>
                    <button class="action-btn" onclick="sharePost(${post.id})">
                        <i class="fas fa-share"></i>
                        <span>Share</span>
                    </button>
                </div>
            </div>
        </div>
    `;
}

function createUserCard(user) {
    const userInitial = user.full_name.charAt(0).toUpperCase();
    const joinDate = new Date(user.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long'
    });
    
    return `
        <div class="user-card" data-user-id="${user.id}">
            <div class="user-card-header">
                <div class="user-card-avatar">${userInitial}</div>
                <div class="user-card-info">
                    <div class="user-card-name">
                        ${user.full_name}
                        ${user.is_verified ? '<i class="fas fa-check-circle user-verified"></i>' : ''}
                    </div>
                    <div class="user-card-username">@${user.username}</div>
                    <div class="user-stats">
                        <span><strong>${user.follower_count || 0}</strong> followers</span>
                        <span><strong>${user.following_count || 0}</strong> following</span>
                        <span><strong>${user.post_count || 0}</strong> posts</span>
                    </div>
                </div>
            </div>
            ${user.bio ? `<div class="user-bio">${user.bio}</div>` : ''}
            <div style="margin-top: 1rem; color: #65676b; font-size: 0.85rem;">
                <i class="fas fa-calendar-alt"></i> Joined ${joinDate}
            </div>
        </div>
    `;
}

function createHashtagCard(hashtag) {
    return `
        <div class="hashtag-card" onclick="searchHashtag('${hashtag.name}')">
            <div class="hashtag-card-header">
                <div class="hashtag-icon">
                    <i class="fas fa-hashtag"></i>
                </div>
                <div>
                    <div class="hashtag-name">${hashtag.name}</div>
                    <div class="hashtag-count">${hashtag.post_count} posts</div>
                </div>
            </div>
        </div>
    `;
}

// Event attachment for dynamic content
function attachEventListeners() {
    // Hashtag clicks
    document.querySelectorAll('.hashtag').forEach(tag => {
        tag.addEventListener('click', function(e) {
            e.preventDefault();
            const hashtag = this.textContent;
            searchHashtag(hashtag);
        });
    });
}

// Action functions
function searchHashtag(hashtag) {
    const cleanHashtag = hashtag.replace('#', '');
    searchInput.value = `#${cleanHashtag}`;
    clearSearchBtn.style.display = 'block';
    performSearch(`#${cleanHashtag}`);
}

function toggleLike(postId) {
    // Simulate like toggle
    const button = event.target.closest('.action-btn');
    const icon = button.querySelector('i');
    const isLiked = button.classList.contains('liked');
    
    if (isLiked) {
        button.classList.remove('liked');
        icon.className = 'fas fa-heart';
    } else {
        button.classList.add('liked');
        icon.className = 'fas fa-heart';
    }
    
    // Here you would typically make an API call to update the like status
    console.log(`${isLiked ? 'Unliked' : 'Liked'} post ${postId}`);
}

function showPostDetails(postId) {
    // Create modal content for post details
    const modalContent = `
        <div class="post-details">
            <h4>Post Details</h4>
            <p>Post ID: ${postId}</p>
            <p>This would show detailed post information, comments, and allow interactions.</p>
            <div style="margin-top: 2rem;">
                <h5>Comments</h5>
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                    <p><strong>@user1:</strong> Great post! Thanks for sharing.</p>
                    <small style="color: #65676b;">2 hours ago</small>
                </div>
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                    <p><strong>@user2:</strong> Very informative content.</p>
                    <small style="color: #65676b;">1 hour ago</small>
                </div>
            </div>
            <div style="margin-top: 2rem;">
                <textarea placeholder="Write a comment..." style="width: 100%; padding: 0.75rem; border: 1px solid #e4e6ea; border-radius: 8px; resize: vertical; min-height: 80px;"></textarea>
                <button style="margin-top: 1rem; background: #4267B2; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; cursor: pointer;">Post Comment</button>
            </div>
        </div>
    `;
    
    modalBody.innerHTML = modalContent;
    postModal.style.display = 'flex';
}

function sharePost(postId) {
    // Simulate share functionality
    if (navigator.share) {
        navigator.share({
            title: 'Check out this post',
            text: 'Found this interesting post on SocialSearch',
            url: window.location.href
        });
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            alert('Link copied to clipboard!');
        });
    }
    console.log(`Shared post ${postId}`);
}

function closeModal() {
    postModal.style.display = 'none';
}

// Load trending hashtags
async function loadTrendingHashtags() {
    try {
        // This would typically fetch from an API endpoint
        // For now, we'll use the static hashtags in the HTML
        console.log('Trending hashtags loaded');
    } catch (error) {
        console.error('Failed to load trending hashtags:', error);
    }
}

// Utility functions
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function timeAgo(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - new Date(date)) / 1000);
    
    if (diffInSeconds < 60) {
        return 'just now';
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `${minutes}m ago`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours}h ago`;
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        return `${days}d ago`;
    }
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
});

// Service worker registration (for future PWA features)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // navigator.serviceWorker.register('/sw.js')
        //     .then(function(registration) {
        //         console.log('SW registered: ', registration);
        //     })
        //     .catch(function(registrationError) {
        //         console.log('SW registration failed: ', registrationError);
        //     });
    });
}