import React, { useState } from 'react';
import { Mail, ArrowLeft, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';

interface ForgotPasswordFormProps {
  onSwitchToLogin: () => void;
  onSwitchToReset: (email: string) => void;
}

export const ForgotPasswordForm: React.FC<ForgotPasswordFormProps> = ({ onSwitchToLogin, onSwitchToReset }) => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const { forgotPassword } = useAuth();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    // Prevent default form submission and propagation
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    
    // Prevent multiple submissions
    if (isLoading) return;
    
    console.log('Submitting forgot password form with email:', email);
    
    try {
      // Clear any previous state
      setIsSubmitted(false);
      
      // Call the API
      const result = await forgotPassword(email);
      console.log('Forgot password result:', result);
      
      if (result.success) {
        // Show success message
        toast({
          title: "Check Your Email",
          description: "We've sent a password reset PIN to your email. Please check your inbox and spam folder.",
        });
        
        // Set submitted state
        setIsSubmitted(true);
        
        // Always navigate to reset password page after successful request
        console.log('Switching to reset password form with email:', email);
        // Use setTimeout to ensure the toast is shown before navigation
        setTimeout(() => {
          onSwitchToReset(email);
        }, 100);
      } else {
        toast({
          title: "Error",
          description: result.message || "Failed to send reset link. Please try again.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Error in handleSubmit:', error);
      toast({
        title: "Error",
        description: "An unexpected error occurred. Please try again.",
        variant: "destructive",
      });
    }
  };

  if (isSubmitted) {
    return (
      <Card className="w-full max-w-md glass-card scale-in">
        <CardHeader className="text-center space-y-4">
          <div className="w-16 h-16 mx-auto bg-gradient-accent rounded-full flex items-center justify-center floating-animation">
            <Mail className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-3xl font-bold gradient-text">Check Your Email</CardTitle>
          <CardDescription className="text-lg">
            We've sent a password reset link to your email address.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="text-center space-y-4">
            <p className="text-sm text-muted-foreground">
              Didn't receive the email? Check your spam folder or try again.
            </p>
            <Button
              onClick={() => onSwitchToReset(email)}
              className="w-full h-12 bg-gradient-accent hover:shadow-glow transition-all duration-300 transform hover:scale-[1.02]"
              type="button"
            >
              I have a reset code
            </Button>
            <button
              onClick={onSwitchToLogin}
              className="flex items-center justify-center space-x-2 text-primary hover:underline text-sm font-medium transition-colors mx-auto"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to sign in</span>
            </button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md glass-card scale-in">
      <CardHeader className="text-center space-y-4">
        <div className="w-16 h-16 mx-auto bg-gradient-accent rounded-full flex items-center justify-center floating-animation">
          <BookOpen className="w-8 h-8 text-white" />
        </div>
        <CardTitle className="text-3xl font-bold gradient-text">Forgot Password?</CardTitle>
        <CardDescription className="text-lg">
          Enter your email and we'll send you a reset link
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email" className="text-sm font-medium">Email</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="pl-10 h-12 bg-white/50 border-white/20 focus:bg-white/80 transition-all duration-300"
                placeholder="Enter your email address"
                required
              />
            </div>
          </div>

          <Button
            type="submit"
            className="w-full h-12 bg-gradient-accent hover:shadow-glow transition-all duration-300 transform hover:scale-[1.02]"
            disabled={isLoading}
          >
            {isLoading ? 'Sending...' : 'Send Reset Link'}
          </Button>
        </form>

        <div className="text-center">
          <button
            onClick={onSwitchToLogin}
            className="flex items-center justify-center space-x-2 text-primary hover:underline text-sm font-medium transition-colors mx-auto"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to sign in</span>
          </button>
        </div>
      </CardContent>
    </Card>
  );
};