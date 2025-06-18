// Update datetime
function updateDateTime() {
    const now = new Date();
    const options = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    };
    document.querySelector('.datetime').textContent = now.toLocaleDateString('en-US', options);
}

setInterval(updateDateTime, 1000);
updateDateTime();

// Simulate detection stats
function updateDetectionStats() {
    document.getElementById('facesDetected').textContent = Math.floor(Math.random() * 1000);
    document.getElementById('threatsDetected').textContent = Math.floor(Math.random() * 10);
    document.getElementById('alertCount').textContent = Math.floor(Math.random() * 5);
}

setInterval(updateDetectionStats, 3000);
updateDetectionStats();

// Show alert toast
function showAlert(message) {
    const toast = document.getElementById('alertToast');
    document.getElementById('toastMessage').textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 5000);
}

function dismissAlert() {
    document.getElementById('alertToast').classList.remove('show');
}

// Search functionality
document.getElementById('searchTarget').addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const cards = document.querySelectorAll('.target-card');
    
    cards.forEach(card => {
        const name = card.querySelector('h3').textContent.toLowerCase();
        if (name.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
});

async function addTargetToGrid(name, imageUrl) {
    const grid = document.getElementById('targetGrid');
    
    const targetCard = document.createElement('div');
    targetCard.className = 'target-card';
    targetCard.dataset.name = name;
    
    targetCard.innerHTML = `
        <div class="target-img">
            <img src="${imageUrl}?${new Date().getTime()}" 
                 onerror="this.src='/static/target_images/default.jpg'" 
                 alt="${name}">
        </div>
        <div class="target-info">
            <h3>${name}</h3>
            <div class="target-status">
                <span class="status unknown">STATUS: UNKNOWN</span>
                <span class="last-seen">LAST SEEN: N/A</span>
            </div>
            <button class="delete-btn" data-target="${name}">Delete</button>
        </div>
    `;
    
    grid.prepend(targetCard);
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const name = document.getElementById('targetName').value.trim();
    const imageFile = document.getElementById('targetImage').files[0];
    
    if (!name) {
        showAlert('Please provide a name for the target');
        return;
    }
    
    if (!imageFile) {
        showAlert('Please select an image file');
        return;
    }
    
    // Client-side validation
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
    if (!validTypes.includes(imageFile.type)) {
        showAlert('Invalid file type. Please upload a JPG, JPEG, or PNG image.');
        return;
    }
    
    // Check file size (client-side, 5MB max)
    if (imageFile.size > 5 * 1024 * 1024) {
        showAlert('Image too large. Maximum size is 5MB.');
        return;
    }
    
    const formData = new FormData();
    formData.append('name', name);
    formData.append('image', imageFile);
    
    try {
        showAlert('Uploading target... Please wait.');
        
        const response = await fetch('/add_target', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to upload');
        }
        
        if (result.success) {
            addTargetToGrid(result.name, result.image_url);
            document.getElementById('addTargetModal').style.display = 'none';
            document.getElementById('targetForm').reset();
            document.getElementById('previewImage').style.display = 'none';
            document.querySelector('.image-preview span').style.display = 'block';
            showAlert(`Target ${result.name} added successfully`);
        } else {
            showAlert(result.error || 'Failed to add target');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showAlert(error.message || 'Failed to add target. Please try again.');
    }
}

async function handleDelete(targetName) {
    if (!confirm(`Are you sure you want to delete ${targetName}? This cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch('/delete_target', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: targetName })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to delete');
        }
        
        if (result.success) {
            document.querySelector(`.target-card[data-name="${targetName}"]`).remove();
            showAlert(`Target ${targetName} deleted successfully`);
        } else {
            showAlert(result.error || 'Failed to delete target');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showAlert(error.message || 'Failed to delete target. Please try again.');
    }
}

function setupEventListeners() {
    // Modal
    document.getElementById('openModal').addEventListener('click', () => {
        document.getElementById('addTargetModal').style.display = 'block';
    });
    
    document.getElementById('closeModal').addEventListener('click', () => {
        document.getElementById('addTargetModal').style.display = 'none';
    });
    
    window.addEventListener('click', (e) => {
        if (e.target === document.getElementById('addTargetModal')) {
            document.getElementById('addTargetModal').style.display = 'none';
        }
    });
    
    // Form submission
    document.getElementById('targetForm').addEventListener('submit', handleFormSubmit);
    
    // Image preview
    document.getElementById('targetImage').addEventListener('change', function() {
        const file = this.files[0];
        const previewImage = document.getElementById('previewImage');
        const previewText = document.querySelector('.image-preview span');
        
        if (file) {
            const reader = new FileReader();
            
            reader.onload = function() {
                previewImage.style.display = 'block';
                previewImage.src = this.result;
                previewText.style.display = 'none';
            };
            
            reader.readAsDataURL(file);
        }
    });
    
    // Delete buttons (delegated event)
    document.getElementById('targetGrid').addEventListener('click', (e) => {
        if (e.target.classList.contains('delete-btn')) {
            handleDelete(e.target.dataset.target);
        }
    });
}

// Initialize everything
document.addEventListener('DOMContentLoaded', () => {
    updateDateTime();
    setInterval(updateDateTime, 1000);
    
    updateDetectionStats();
    setupEventListeners();
});