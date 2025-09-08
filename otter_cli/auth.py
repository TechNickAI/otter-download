"""
Authentication module for Otter.ai API
Handles login and basic API operations with proper error handling
"""

import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

try:
    from otterai import OtterAI, OtterAIException
except ImportError:
    # Fallback if otterai is not installed
    print("⚠️  otterai package not found. Please install with: pip install -r requirements.txt")
    raise


class OtterAuth:
    """Handles Otter.ai authentication and API calls"""
    
    def __init__(self):
        self.otter: Optional[OtterAI] = None
        self.authenticated: bool = False
        
    def login(self, username: str, password: str) -> bool:
        """
        Attempt to login to Otter.ai
        
        Args:
            username: Otter.ai username/email
            password: Otter.ai password
            
        Returns:
            True if authentication successful, False otherwise
            
        Raises:
            Exception: For network or API errors
        """
        try:
            self.otter = OtterAI()
            self.otter.login(username, password)
            self.authenticated = True
            return True
            
        except OtterAIException as e:
            # Handle specific Otter API errors
            if "unauthorized" in str(e).lower() or "invalid" in str(e).lower():
                self.authenticated = False
                return False
            else:
                # Re-raise for other API errors
                raise Exception(f"Otter.ai API error: {str(e)}")
                
        except Exception as e:
            # Handle network or other errors
            logger.exception("Network or connection error during login")
            raise Exception(f"Connection error: {str(e)}")
    
    def get_speeches(self) -> List[Dict[str, Any]]:
        """
        Get list of user's speeches
        
        Returns:
            List of speech dictionaries
            
        Raises:
            Exception: If not authenticated or API error
        """
        if not self.authenticated or not self.otter:
            raise Exception("Not authenticated. Please login first.")
            
        try:
            response = self.otter.get_speeches()
            
            # Handle case where API returns None or empty
            if response is None:
                return []
                
            # The otterai API returns {'status': status_code, 'data': actual_data}
            if isinstance(response, dict) and 'data' in response:
                data = response['data']
                
                # Handle different data structures
                if isinstance(data, dict):
                    # Check for common patterns
                    if 'speeches' in data:
                        speeches = data['speeches']
                    elif 'results' in data:
                        speeches = data['results']  
                    else:
                        # The data might be the speeches directly
                        speeches = data
                    
                    if isinstance(speeches, list):
                        return speeches
                    else:
                        return []
                        
                elif isinstance(data, list):
                    return data
                else:
                    return []
            else:
                # Fallback for unexpected response format
                return []
                
        except OtterAIException as e:
            logger.exception("Failed to fetch speeches - OtterAI API error")
            raise Exception(f"Failed to fetch speeches: {str(e)}")
        except Exception as e:
            logger.exception("Error fetching speeches - general error")
            raise Exception(f"Error fetching speeches: {str(e)}")
    
    def get_speeches_with_size(self, page_size: int = 45, folder: int = 0, source: str = "owned") -> List[Dict[str, Any]]:
        """
        Get speeches with specific page size for testing pagination
        """
        if not self.authenticated or not self.otter:
            raise Exception("Not authenticated. Please login first.")
            
        try:
            response = self.otter.get_speeches(folder=folder, page_size=page_size, source=source)
            
            # Same parsing logic but without debug prints
            if response is None:
                return []
                
            if isinstance(response, dict) and 'data' in response:
                data = response['data']
                
                if isinstance(data, dict):
                    if 'speeches' in data:
                        speeches = data['speeches']
                    elif 'results' in data:
                        speeches = data['results']  
                    else:
                        speeches = data
                        
                    if isinstance(speeches, list):
                        return speeches
                    else:
                        return []
                        
                elif isinstance(data, list):
                    return data
                else:
                    return []
            else:
                    return []
                
        except OtterAIException as e:
            logger.exception("Failed to fetch speeches with specific size - OtterAI API error")
            raise Exception(f"Failed to fetch speeches: {str(e)}")
        except Exception as e:
            logger.exception("Error fetching speeches with specific size - general error")
            raise Exception(f"Error fetching speeches: {str(e)}")
    
    def get_all_speeches(self, folder: int = 0, source: str = "owned") -> List[Dict[str, Any]]:
        """
        Get ALL speeches using pagination, following end_of_list indicator
        
        Returns:
            Complete list of all speech dictionaries
        """
        if not self.authenticated or not self.otter:
            raise Exception("Not authenticated. Please login first.")
            
        all_speeches = []
        last_load_ts = None
        page_count = 0
        
        try:
            while True:
                page_count += 1
                
                # Get a batch of speeches with large page size
                response = self.otter.get_speeches(folder=folder, page_size=500, source=source)
                
                if response is None or not isinstance(response, dict) or 'data' not in response:
                    break
                    
                data = response['data']
                
                # Extract speeches from this batch
                if isinstance(data, dict):
                    batch_speeches = data.get('speeches', [])
                    end_of_list = data.get('end_of_list', True)
                    last_load_ts = data.get('last_load_ts')
                    
                    if isinstance(batch_speeches, list):
                        all_speeches.extend(batch_speeches)
                    
                    # Check if we've reached the end
                    if end_of_list:
                        break
                        
                    # Safety check to prevent infinite loops
                    if page_count > 100:  # Max 50,000 speeches
                        print(f"⚠️  Safety limit reached: {page_count} pages, {len(all_speeches)} speeches")
                        break
                else:
                    break
            
            return all_speeches
            
        except OtterAIException as e:
            logger.exception("Failed to fetch all speeches - OtterAI API error")
            raise Exception(f"Failed to fetch all speeches: {str(e)}")
        except Exception as e:
            logger.exception("Error fetching all speeches - general error")
            raise Exception(f"Error fetching all speeches: {str(e)}")
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get user information
        
        Returns:
            User info dictionary
        """
        if not self.authenticated or not self.otter:
            raise Exception("Not authenticated. Please login first.")
            
        try:
            return self.otter.get_user()
        except Exception as e:
            raise Exception(f"Failed to get user info: {str(e)}")
