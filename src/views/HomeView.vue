<template>
    <div class="content-section">
      <h1>{{ campaignName }}</h1>
      <p class="intro-text">
        Welcome to the central hub for our adventures in the realm of {{ worldName }}. 
      </p>
      
      <!-- Campaign banner image -->
      <div class="banner-container">
        <img src="../assets/gaslamp.jpg" alt="Campaign Banner" class="campaign-banner">
      </div>
      
      <div class="campaign-quick-info">
        <div class="info-card">
          <h3 class="fancy-title">Current Location</h3>
          <p>{{ currentLocation }}</p>
        </div>
        
        <div class="info-card">
          <h3 class="fancy-title">Current Quest</h3>
          <p>{{ currentQuest }}</p>
        </div>
        
        <div class="info-card">
          <h3 class="fancy-title">Next Session</h3>
          <p>{{ nextSession }}</p>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'HomeView',
    data() {
      return {
        campaignName: '<Untitled Gaslamp Adventures>',
        worldName: 'New Aetherwick (TBD)',
        currentLocation: 'Session 0',
        currentQuest: 'Session 0',
        nextSession: 'Sunday, May 4th at 1:00 PM'
      };
    }
  }
  </script>
  
  <style scoped>
  h1 {
    text-align: center;
    margin-bottom: 1em;
    font-size: 3em;
  }
  
  .intro-text {
    font-size: 1.1em;
    max-width: 800px;
    margin: 0 auto 2em;
    text-align: center;
  }
  
  .banner-placeholder {
    display: none; /* Hide the placeholder */
  }
  
  .banner-container {
    width: 100%;
    margin: 2em 0;
    border-radius: 8px;
    overflow: hidden;
  }
  
  .campaign-banner {
    width: 100%;
    height: auto;
    object-fit: cover;
    border-radius: 8px;
    border: 1px solid var(--border-color);
  }
  
  .campaign-quick-info {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-top: 3rem;
  }
  
  .info-card {
    background: var(--gradient-primary);
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    text-align: center;
  }
  
  .info-card h3 {
    margin-top: 0;
    margin-bottom: 1rem;
  }
  
  @media (max-width: 768px) {
    .campaign-quick-info {
      grid-template-columns: 1fr;
    }
  }
  </style>