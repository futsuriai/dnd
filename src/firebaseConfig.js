// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getFirestore, connectFirestoreEmulator } from "firebase/firestore";
import { getAnalytics } from "firebase/analytics";

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyA_43HQWquAKfK8YvHFn5VG38Jm47GgHG0",
  authDomain: "dnd-campaign2.firebaseapp.com",
  projectId: "dnd-campaign2",
  storageBucket: "dnd-campaign2.firebasestorage.app",
  messagingSenderId: "939118303196",
  appId: "1:939118303196:web:4f0b234d914a1c66b66119",
  measurementId: "G-DD7F4C1FQ5"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
let analytics = null;
try {
  analytics = getAnalytics(app);
} catch (e) {
  console.log('Analytics not supported in this environment');
}

// Set up Google Auth provider
const googleProvider = new GoogleAuthProvider();

// Use emulators for local development if needed
// For Vite, use import.meta.env instead of process.env
const isDevelopment = import.meta.env.MODE === 'development';
const useEmulators = import.meta.env.VITE_USE_EMULATORS === 'true';

if (isDevelopment && useEmulators) {
  // connectFirestoreEmulator(db, 'localhost', 8080);
  // connectAuthEmulator(auth, 'http://localhost:9099');
  console.log('Using Firebase emulators for development');
}

// Check if we're using dev or prod environment
// This will help determine which Firestore collection prefix to use
const isDev = import.meta.env.MODE !== 'production';
const dbPrefix = isDev ? 'dev_' : 'prod_';

export { 
  auth, 
  db, 
  googleProvider,
  dbPrefix 
};
