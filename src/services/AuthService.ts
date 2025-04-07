// AuthService.ts - Authentication service for the application
import { Auth, User, UserCredential, GoogleAuthProvider } from 'firebase/auth';
import { auth, googleProvider } from '../firebaseConfig';
import { 
  signInWithPopup, 
  signOut as firebaseSignOut,
  onAuthStateChanged
} from 'firebase/auth';
import { db } from '../firebaseConfig';
import { doc, getDoc, DocumentSnapshot, DocumentData } from 'firebase/firestore';

// Type for auth state listener callback
type AuthStateListener = (user: User | null, isEditor: boolean) => void;

// List of authorized editor email addresses
// Add your Google email address here to grant yourself editor permissions
const AUTHORIZED_EDITORS: string[] = [
  'futsuriai@gmail.com'
];

class AuthService {
  private user: User | null;
  private isEditor: boolean;
  private listeners: AuthStateListener[];
  
  constructor() {
    this.user = null;
    this.isEditor = false;
    this.listeners = [];
    
    // Set up auth state listener
    onAuthStateChanged(auth, async (user) => {
      this.user = user;
      
      if (user) {
        console.log("My Admin UID is:", auth.currentUser?.uid);
        
        // Check if user is in the authorized editors list
        this.isEditor = AUTHORIZED_EDITORS.includes(user.email || '');
        
        // If not in the hardcoded list, check Firestore for dynamic permissions
        if (!this.isEditor && user.email) {
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
  
  async checkEditorPermissionsInFirestore(email: string): Promise<boolean> {
    try {
      // Check the 'editors' collection for this user
      const editorRef = doc(db, 'editors', email);
      const editorDoc: DocumentSnapshot<DocumentData> = await getDoc(editorRef);
      
      return editorDoc.exists();
    } catch (error) {
      console.error('Error checking editor permissions:', error);
      return false;
    }
  }
  
  // Sign in with Google
  async signInWithGoogle(): Promise<User> {
    try {
      const result: UserCredential = await signInWithPopup(auth, googleProvider);
      return result.user;
    } catch (error) {
      console.error('Error signing in with Google:', error);
      throw error;
    }
  }
  
  // Sign out
  async signOut(): Promise<void> {
    try {
      await firebaseSignOut(auth);
    } catch (error) {
      console.error('Error signing out:', error);
      throw error;
    }
  }
  
  // Get current user
  getCurrentUser(): User | null {
    return this.user;
  }
  
  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!this.user;
  }
  
  // Check if user is an editor
  isAuthorizedEditor(): boolean {
    return this.isAuthenticated() && this.isEditor;
  }
  
  // Add auth state change listener
  addAuthListener(callback: AuthStateListener): () => void {
    this.listeners.push(callback);
    
    // Call the callback immediately with current state
    callback(this.user, this.isEditor);
    
    // Return an unsubscribe function
    return () => {
      this.listeners = this.listeners.filter(listener => listener !== callback);
    };
  }
  
  // Notify all listeners of auth state change
  notifyListeners(): void {
    this.listeners.forEach(callback => callback(this.user, this.isEditor));
  }
}

// Create singleton instance
const authService = new AuthService();

export default authService;