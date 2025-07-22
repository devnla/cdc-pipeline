// API Configuration
const API_BASE_URL = 'http://localhost:8000';
const AUTOCOMPLETE_DEBOUNCE_MS = 200;
const MIN_AUTOCOMPLETE_LENGTH = 2;

// Global state
let currentTab = 'all';
let currentQuery = '';
let searchTimeout = null;
let autocompleteTimeout = null;
let currentSuggestions = [];
let selectedSuggestionIndex = -1;
let analyticsCharts = {};
let trendingData = {};
let analyticsData = {};

// DOM Elements
const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearch');
const searchSuggestions = document.getElementById('searchSuggestions');
const suggestions = document.getElementById('suggestions');
const tabButtons = document.querySelectorAll('.tab-btn');
const loadingSpinner = document.getElementById('loadingSpinner');
const welcomeMessage = document.getElementById('welcomeMessage');
const resultsContainer = document.getElementById('resultsContainer');
const resultsContent = document.getElementById('resultsContent');
const resultsTitle = document.getElementById('resultsTitle');
const resultsCount = document.getElementById('resultsCount');
const trendingHashtags = document.querySelectorAll('.hashtag-tag');
const noResults = document.getElementById('noResults');
const postModal = document.getElementById('postModal');
const modalBody = document.getElementById('modalBody');
const trendingSection = document.getElementById('trendingSection');
const analyticsSection = document.getElementById('analyticsSection');
const trendingHashtagsList = document.getElementById('trendingHashtagsList');
const trendingPostsList = document.getElementById('trendingPostsList');
const themeToggle = document.getElementById('themeToggle');

// Theme Management
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = themeToggle.querySelector('i');
    if (theme === 'dark') {
        icon.className = 'fas fa-sun';
        themeToggle.title = 'Switch to light mode';
    } else {
        icon.className = 'fas fa-moon';
        themeToggle.title = 'Switch to dark mode';
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    initializeEventListeners();
    loadTrendingHashtags();
    
    // Initialize AOS (Animate On Scroll)
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-out',
            once: true,
            offset: 100
        });
    }
});

// Event Listeners
function initializeEventListeners() {
    // Search input events
    searchInput.addEventListener('input', handleSearchInput);
    searchInput.addEventListener('keypress', handleSearchKeypress);
    searchInput.addEventListener('focus', showSearchSuggestions);
    searchInput.addEventListener('blur', hideSearchSuggestions);
    
    // Clear search button
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', clearSearch);
    }
    
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
    
    // Initialize analytics controls
    initializeAnalyticsControls();
    
    // Theme toggle event
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

// Search functionality
function handleSearchInput(e) {
    const query = e.target.value.trim();
    
    // Show/hide clear button
    if (clearSearchBtn) {
        clearSearchBtn.style.display = query ? 'block' : 'none';
    }
    
    // Handle autocomplete
    clearTimeout(autocompleteTimeout);
    if (query.length >= MIN_AUTOCOMPLETE_LENGTH) {
        autocompleteTimeout = setTimeout(() => {
            fetchAutocompleteSuggestions(query);
        }, AUTOCOMPLETE_DEBOUNCE_MS);
    } else {
        hideSearchSuggestions();
    }
    
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
        e.preventDefault();
        if (selectedSuggestionIndex >= 0 && currentSuggestions.length > 0) {
            // Select the highlighted suggestion
            selectSuggestion(currentSuggestions[selectedSuggestionIndex]);
        } else {
            const query = e.target.value.trim();
            if (query) {
                hideSearchSuggestions();
                performSearch(query);
            }
        }
    } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        navigateSuggestions(1);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        navigateSuggestions(-1);
    } else if (e.key === 'Escape') {
        hideSearchSuggestions();
        selectedSuggestionIndex = -1;
    }
}

function clearSearch() {
    searchInput.value = '';
    if (clearSearchBtn) {
        clearSearchBtn.style.display = 'none';
    }
    currentQuery = '';
    showWelcomeMessage();
    searchInput.focus();
}

function showSearchSuggestions() {
    if (currentSuggestions.length > 0) {
        searchSuggestions.style.display = 'block';
    }
}

function hideSearchSuggestions() {
    setTimeout(() => {
        searchSuggestions.style.display = 'none';
        selectedSuggestionIndex = -1;
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
    
    // Handle different tab types
    if (tabName === 'trending') {
        showTrendingSection();
    } else if (tabName === 'analytics') {
        showAnalyticsSection();
    } else {
        // Regular search tabs
        hideAllSections();
        if (currentQuery) {
            performSearch(currentQuery);
        } else {
            showWelcomeMessage();
        }
    }
}

// Hashtag functionality
function handleHashtagClick(e) {
    const hashtag = e.target.dataset.hashtag || e.target.textContent;
    const cleanHashtag = hashtag.replace('#', '');
    
    searchInput.value = `#${cleanHashtag}`;
    if (clearSearchBtn) {
        clearSearchBtn.style.display = 'block';
    }
    performSearch(`#${cleanHashtag}`);
}

// Autocomplete functionality
async function fetchAutocompleteSuggestions(query) {
    try {
        // Use typo-tolerant autocomplete for better suggestions
        const response = await fetch(`${API_BASE_URL}/autocomplete/typo-tolerant?q=${encodeURIComponent(query)}&limit=6`);
        if (!response.ok) {
            console.warn('Typo-tolerant autocomplete request failed, falling back to regular autocomplete:', response.status);
            // Fallback to regular autocomplete
            return await fetchRegularAutocompleteSuggestions(query);
        }
        
        const data = await response.json();
        currentSuggestions = [];
        
        // Process typo-tolerant suggestions
        if (data.suggestions) {
            // Add users with similarity indicators
            if (data.suggestions.users) {
                data.suggestions.users.forEach(user => {
                    const similarity = user.metadata?.similarity || 1;
                    const displayName = user.display_text || `${user.metadata?.full_name || user.value} (@${user.value})`;
                    currentSuggestions.push({
                        type: 'user',
                        text: `@${user.value}`,
                        display: similarity < 0.9 ? `${displayName} (did you mean?)` : displayName,
                        icon: 'fas fa-user',
                        data: user,
                        similarity: similarity
                    });
                });
            }
            
            // Add hashtags with similarity indicators
            if (data.suggestions.hashtags) {
                data.suggestions.hashtags.forEach(hashtag => {
                    const similarity = hashtag.metadata?.similarity || 1;
                    const hashtagName = hashtag.metadata?.hashtag || hashtag.value.replace('#', '');
                    const postCount = hashtag.metadata?.post_count || 0;
                    currentSuggestions.push({
                        type: 'hashtag',
                        text: `#${hashtagName}`,
                        display: similarity < 0.9 ? `#${hashtagName} (${postCount} posts) - did you mean?` : `#${hashtagName} (${postCount} posts)`,
                        icon: 'fas fa-hashtag',
                        data: hashtag,
                        similarity: similarity
                    });
                });
            }
            
            // Add content terms
            if (data.suggestions.content) {
                data.suggestions.content.forEach(content => {
                    const similarity = content.metadata?.similarity || 1;
                    currentSuggestions.push({
                        type: 'content',
                        text: content.value,
                        display: similarity < 0.9 ? `'${content.value}' in posts (did you mean?)` : content.display_text,
                        icon: 'fas fa-search',
                        data: content,
                        similarity: similarity
                    });
                });
            }
            
            // Add related terms
            if (data.suggestions.related_terms) {
                data.suggestions.related_terms.forEach(term => {
                    currentSuggestions.push({
                        type: 'related',
                        text: term.value,
                        display: term.display_text,
                        icon: 'fas fa-lightbulb',
                        data: term,
                        similarity: 1
                    });
                });
            }
        }
        
        // Sort suggestions by similarity and score
        currentSuggestions.sort((a, b) => {
            if (a.similarity !== b.similarity) {
                return b.similarity - a.similarity;
            }
            return (b.data?.score || 0) - (a.data?.score || 0);
        });
        
        displayAutocompleteSuggestions();
    } catch (error) {
        console.error('Typo-tolerant autocomplete error:', error);
        // Fallback to regular autocomplete
        await fetchRegularAutocompleteSuggestions(query);
    }
}

// Fallback function for regular autocomplete
async function fetchRegularAutocompleteSuggestions(query) {
    try {
        const response = await fetch(`${API_BASE_URL}/autocomplete/suggestions?q=${encodeURIComponent(query)}&limit=8`);
        if (!response.ok) {
            console.warn('Regular autocomplete request failed:', response.status);
            return;
        }
        
        const data = await response.json();
        currentSuggestions = [];
        
        // Combine different types of suggestions
        if (data.suggestions) {
            if (data.suggestions.users) {
                data.suggestions.users.forEach(user => {
                    currentSuggestions.push({
                        type: 'user',
                        text: `@${user.username}`,
                        display: `${user.full_name} (@${user.username})`,
                        icon: 'fas fa-user',
                        data: user,
                        similarity: 1
                    });
                });
            }
            
            if (data.suggestions.hashtags) {
                data.suggestions.hashtags.forEach(hashtag => {
                    currentSuggestions.push({
                        type: 'hashtag',
                        text: `#${hashtag.name}`,
                        display: `#${hashtag.name} (${hashtag.post_count} posts)`,
                        icon: 'fas fa-hashtag',
                        data: hashtag,
                        similarity: 1
                    });
                });
            }
            
            if (data.suggestions.content) {
                data.suggestions.content.forEach(content => {
                    currentSuggestions.push({
                        type: 'content',
                        text: content.text,
                        display: content.text,
                        icon: 'fas fa-search',
                        data: content,
                        similarity: 1
                    });
                });
            }
        }
        
        displayAutocompleteSuggestions();
    } catch (error) {
        console.error('Regular autocomplete error:', error);
    }
}

function displayAutocompleteSuggestions() {
    if (currentSuggestions.length === 0) {
        hideSearchSuggestions();
        return;
    }
    
    let html = '';
    currentSuggestions.forEach((suggestion, index) => {
        const isSelected = index === selectedSuggestionIndex;
        
        // Determine CSS classes based on suggestion type and similarity
        let cssClasses = ['suggestion-item'];
        if (isSelected) cssClasses.push('selected');
        
        // Add type-specific classes
        if (suggestion.type === 'related') {
            cssClasses.push('related-term');
        } else if (suggestion.similarity && suggestion.similarity < 0.9) {
            cssClasses.push('typo-suggestion', 'low-similarity');
        }
        
        // Create similarity indicator
        let similarityIndicator = '';
        if (suggestion.similarity && suggestion.similarity < 0.9) {
            const percentage = Math.round(suggestion.similarity * 100);
            similarityIndicator = `<span class="suggestion-similarity">${percentage}% match</span>`;
        }
        
        html += `
            <div class="${cssClasses.join(' ')}" 
                 data-index="${index}" 
                 onclick="selectSuggestion(currentSuggestions[${index}])">
                <i class="${suggestion.icon}"></i>
                <span>${suggestion.display}${similarityIndicator}</span>
            </div>
        `;
    });
    
    searchSuggestions.innerHTML = html;
    showSearchSuggestions();
}

function navigateSuggestions(direction) {
    if (currentSuggestions.length === 0) return;
    
    selectedSuggestionIndex += direction;
    
    if (selectedSuggestionIndex < 0) {
        selectedSuggestionIndex = currentSuggestions.length - 1;
    } else if (selectedSuggestionIndex >= currentSuggestions.length) {
        selectedSuggestionIndex = 0;
    }
    
    displayAutocompleteSuggestions();
}

function selectSuggestion(suggestion) {
    searchInput.value = suggestion.text;
    if (clearSearchBtn) {
        clearSearchBtn.style.display = 'block';
    }
    hideSearchSuggestions();
    performSearch(suggestion.text);
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
    const response = await fetch(`${API_BASE_URL}/search/posts?q=${encodeURIComponent(query)}&size=20`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    });
    if (!response.ok) {
        console.error(`Search posts failed: ${response.status} ${response.statusText}`);
        throw new Error('Failed to search posts');
    }
    return await response.json();
}

async function searchUsers(query) {
    const response = await fetch(`${API_BASE_URL}/search/users?q=${encodeURIComponent(query)}&size=20`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    });
    if (!response.ok) {
        console.error(`Search users failed: ${response.status} ${response.statusText}`);
        throw new Error('Failed to search users');
    }
    return await response.json();
}

async function searchHashtags(query) {
    const cleanQuery = query.replace('#', '');
    const response = await fetch(`${API_BASE_URL}/search/hashtags?q=${encodeURIComponent(cleanQuery)}&size=20`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    });
    if (!response.ok) {
        console.error(`Search hashtags failed: ${response.status} ${response.statusText}`);
        throw new Error('Failed to search hashtags');
    }
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
    trendingSection.style.display = 'none';
    analyticsSection.style.display = 'none';
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
    if (clearSearchBtn) {
        clearSearchBtn.style.display = 'block';
    }
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
        const response = await fetch(`${API_BASE_URL}/search/trending/hashtags?limit=10`);
        if (!response.ok) {
            console.warn('Failed to load trending hashtags, using defaults');
            return;
        }
        
        const hashtags = await response.json();
        updateTrendingHashtagsDisplay(hashtags);
    } catch (error) {
        console.error('Failed to load trending hashtags:', error);
    }
}

function updateTrendingHashtagsDisplay(hashtags) {
    const trendingContainer = document.querySelector('.trending-hashtags');
    if (!trendingContainer || hashtags.length === 0) return;
    
    let html = '<h3>Trending Hashtags</h3>';
    hashtags.forEach(hashtag => {
        html += `
            <span class="hashtag-tag" data-hashtag="${hashtag.name}">
                #${hashtag.name}
                <small>(${hashtag.post_count})</small>
            </span>
        `;
    });
    
    trendingContainer.innerHTML = html;
    
    // Re-attach event listeners for new hashtag tags
    trendingContainer.querySelectorAll('.hashtag-tag').forEach(tag => {
        tag.addEventListener('click', handleHashtagClick);
    });
}

// Section display functions
function showTrendingSection() {
    hideAllSections();
    trendingSection.style.display = 'block';
    loadTrendingData();
}

function showAnalyticsSection() {
    hideAllSections();
    analyticsSection.style.display = 'block';
    loadAnalyticsData();
}

// Trending data functions
async function loadTrendingData() {
    try {
        // Load trending hashtags
        const hashtagsResponse = await fetch(`${API_BASE_URL}/search/trending/hashtags`);
        if (hashtagsResponse.ok) {
            const hashtagsData = await hashtagsResponse.json();
            displayTrendingHashtags(hashtagsData.hashtags || []);
        }
        
        // Load trending posts
        const postsResponse = await fetch(`${API_BASE_URL}/analytics/trending`);
        if (postsResponse.ok) {
            const postsData = await postsResponse.json();
            displayTrendingPosts(postsData.posts || []);
        }
    } catch (error) {
        console.error('Error loading trending data:', error);
    }
}

function displayTrendingHashtags(hashtags) {
    if (!trendingHashtagsList) return;
    
    trendingHashtagsList.innerHTML = '';
    
    hashtags.slice(0, 10).forEach((hashtag, index) => {
        const hashtagElement = document.createElement('div');
        hashtagElement.className = 'trending-hashtag-item';
        hashtagElement.innerHTML = `
            <span class="hashtag-rank">#${index + 1}</span>
            <span class="hashtag-name">#${hashtag.hashtag}</span>
            <span class="hashtag-count">${formatNumber(hashtag.count)} posts</span>
        `;
        hashtagElement.addEventListener('click', () => {
            searchInput.value = `#${hashtag.hashtag}`;
            currentTab = 'hashtags';
            document.querySelector('[data-tab="hashtags"]').classList.add('active');
            performSearch(`#${hashtag.hashtag}`);
        });
        trendingHashtagsList.appendChild(hashtagElement);
    });
}

function displayTrendingPosts(posts) {
    if (!trendingPostsList) return;
    
    trendingPostsList.innerHTML = '';
    
    posts.slice(0, 5).forEach(post => {
        const postElement = createPostCard(post);
        postElement.classList.add('trending-post-card');
        trendingPostsList.appendChild(postElement);
    });
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

// Analytics functions
async function loadAnalyticsData() {
    try {
        const timeRange = document.getElementById('timeRange')?.value || '7d';
        
        // Load analytics data
        const analyticsResponse = await fetch(`${API_BASE_URL}/analytics/posts?time_range=${timeRange}`);
        if (analyticsResponse.ok) {
            const data = await analyticsResponse.json();
            updateAnalyticsMetrics(data);
            updateAnalyticsCharts(data);
        }
        
        // Load engagement summary
        const engagementResponse = await fetch(`${API_BASE_URL}/analytics/engagement-summary?time_range=${timeRange}`);
        if (engagementResponse.ok) {
            const engagementData = await engagementResponse.json();
            updateEngagementCharts(engagementData);
        }
    } catch (error) {
        console.error('Error loading analytics data:', error);
    }
}

function updateAnalyticsMetrics(data) {
    const metrics = data.metrics || {};
    
    document.getElementById('totalPosts').textContent = formatNumber(metrics.total_posts || 0);
    document.getElementById('avgLikes').textContent = formatNumber(metrics.avg_likes || 0);
    document.getElementById('avgComments').textContent = formatNumber(metrics.avg_comments || 0);
    document.getElementById('topHashtags').textContent = (metrics.top_hashtags && metrics.top_hashtags.length > 0) ? metrics.top_hashtags[0].hashtag : 'N/A';
}

function updateAnalyticsCharts(data) {
    if (typeof Chart === 'undefined') return;
    
    // Posts over time chart
    const postsCtx = document.getElementById('postsChart');
    if (postsCtx && data.posts_over_time) {
        if (analyticsCharts.postsChart) {
            analyticsCharts.postsChart.destroy();
        }
        
        analyticsCharts.postsChart = new Chart(postsCtx, {
            type: 'line',
            data: {
                labels: data.posts_over_time.map(item => new Date(item.date).toLocaleDateString()),
                datasets: [{
                    label: 'Posts',
                    data: data.posts_over_time.map(item => item.count),
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Popular hashtags chart
    const hashtagsCtx = document.getElementById('hashtagsChart');
    if (hashtagsCtx && data.top_hashtags) {
        if (analyticsCharts.hashtagsChart) {
            analyticsCharts.hashtagsChart.destroy();
        }
        
        analyticsCharts.hashtagsChart = new Chart(hashtagsCtx, {
            type: 'doughnut',
            data: {
                labels: data.top_hashtags.slice(0, 5).map(item => `#${item.hashtag}`),
                datasets: [{
                    data: data.top_hashtags.slice(0, 5).map(item => item.count),
                    backgroundColor: [
                        '#007bff',
                        '#28a745',
                        '#ffc107',
                        '#dc3545',
                        '#6f42c1'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

function updateEngagementCharts(data) {
    if (typeof Chart === 'undefined') return;
    
    // Engagement distribution chart
    const engagementCtx = document.getElementById('engagementChart');
    if (engagementCtx && data.engagement_distribution) {
        if (analyticsCharts.engagementChart) {
            analyticsCharts.engagementChart.destroy();
        }
        
        analyticsCharts.engagementChart = new Chart(engagementCtx, {
            type: 'bar',
            data: {
                labels: ['Likes', 'Comments', 'Shares'],
                datasets: [{
                    label: 'Total Engagement',
                    data: [
                        data.engagement_distribution.total_likes || 0,
                        data.engagement_distribution.total_comments || 0,
                        data.engagement_distribution.total_shares || 0
                    ],
                    backgroundColor: [
                        '#007bff',
                        '#28a745',
                        '#ffc107'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

// Event listeners for analytics controls
function initializeAnalyticsControls() {
    const timeRangeSelect = document.getElementById('timeRange');
    if (timeRangeSelect) {
        timeRangeSelect.addEventListener('change', () => {
            if (currentTab === 'analytics') {
                loadAnalyticsData();
            }
        });
    }
    
    // Refresh buttons
    document.querySelectorAll('.refresh-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            if (currentTab === 'trending') {
                loadTrendingData();
            } else if (currentTab === 'analytics') {
                loadAnalyticsData();
            }
        });
    });
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