<template>
    <div class="content-section">
      <h1>{{ campaignName }}</h1>
      <p class="intro-text">
        Welcome to the central hub for our adventures in the realm of {{ worldName }}. 
        Here you'll find information about the brave heroes, important NPCs, the world's 
        rich history, magical items discovered, and chronicles of our journey.
      </p>
      
      <!-- Placeholder for campaign banner -->
      <div class="banner-placeholder">
        <div class="placeholder-text">Campaign Banner</div>
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
        campaignName: '<Campaign 2>',
        worldName: '<Unknown>',
        currentLocation: 'Session 0',
        currentQuest: 'Session 0',
        nextSession: 'Sunday, April 6th at 2:00 PM'
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
    width: 100%;
    height: 250px;
    margin: 2em 0;
    background: linear-gradient(135deg, var(--color-background) 0%, var(--color-surface) 100%);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px dashed var(--border-color);
  }
  
  .placeholder-text {
    font-family: var(--font-accent);
    color: var(--color-text-muted);
    font-size: 1.2em;
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