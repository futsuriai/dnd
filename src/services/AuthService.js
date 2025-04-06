import { auth, googleProvider } from '../firebaseConfig';
import { 
  signInWithPopup, 
  signOut as firebaseSignOut,
  onAuthStateChanged
} from 'firebase/auth';
import { db } from '../firebaseConfig';
import { doc, getDoc } from 'firebase/firestore';

// List of authorized editor email addresses
// Add your Google email address here to grant yourself editor permissions
const AUTHORIZED_EDITORS = [
  'futsuriai@gmail.com'
];

class AuthService {
  constructor() {
    this.user = null;
    this.isEditor = false;
    this.listeners = [];
    
    // Set up auth state listener
    onAuthStateChanged(auth, async (user) => {
      this.user = user;
      console.log("My Admin UID is:", auth.currentUser.uid);

      if (user) {
        // Check if user is in the authorized editors list
        this.isEditor = AUTHORIZED_EDITORS.includes(user.email);
        
        // If not in the hardcoded list, check Firestore for dynamic permissions
        if (!this.isEditor) {
          this.isEditor = await this.checkEditorPermissionsInFirestore(user.email);
        }
        
        console.log(`User ${user.email} logged in. Editor access: ${this.isEditor}`);
      } else {
        this.isEditor = false;
      }
      
      // Notify all listeners
      this.notifyListeners();
    });
  }
  
  async checkEditorPermissionsInFirestore(email) {
    try {
      // Check the 'editors' collection for this user
      const editorRef = doc(db, 'editors', email);
      const editorDoc = await getDoc(editorRef);
      
      return editorDoc.exists();
    } catch (error) {
      console.error('Error checking editor permissions:', error);
      return false;
    }
  }
  
  // Sign in with Google
  async signInWithGoogle() {
    try {
      const result = await signInWithPopup(auth, googleProvider);
      return result.user;
    } catch (error) {
      console.error('Error signing in with Google:', error);
      throw error;
    }
  }
  
  // Sign out
  async signOut() {
    try {
      await firebaseSignOut(auth);
    } catch (error) {
      console.error('Error signing out:', error);
      throw error;
    }
  }
  
  // Get current user
  getCurrentUser() {
    return this.user;
  }
  
  // Check if user is authenticated
  isAuthenticated() {
    return !!this.user;
  }
  
  // Check if user is an editor
  isAuthorizedEditor() {
    return this.isAuthenticated() && this.isEditor;
  }
  
  // Add auth state change listener
  addAuthListener(callback) {
    this.listeners.push(callback);
    
    // Call the callback immediately with current state
    callback(this.user, this.isEditor);
    
    // Return an unsubscribe function
    return () => {
      this.listeners = this.listeners.filter(listener => listener !== callback);
    };
  }
  
  // Notify all listeners of auth state change
  notifyListeners() {
    this.listeners.forEach(callback => callback(this.user, this.isEditor));
  }
}

// Create singleton instance
const authService = new AuthService();

export default authService;