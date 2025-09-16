"""
Authentication module for Otter.ai API
Handles login and basic API operations with proper error handling
"""

import logging
import json
from typing import List, Dict, Optional, Any

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
            logger.info("🔍 Calling otter.get_speeches()...")
            response = self.otter.get_speeches()
            
            logger.info(f"📡 Raw API response type: {type(response)}")
            logger.info(f"📡 Raw API response: {json.dumps(response, indent=2, default=str) if response else 'None'}")
            
            # Handle case where API returns None or empty
            if response is None:
                logger.warning("⚠️ API returned None response")
                return []
                
            # The otterai API returns {'status': status_code, 'data': actual_data}
            if isinstance(response, dict) and 'data' in response:
                data = response['data']
                logger.info(f"📊 Response data type: {type(data)}")
                logger.info(f"📊 Response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # Handle different data structures
                if isinstance(data, dict):
                    # Check for common patterns
                    if 'speeches' in data:
                        speeches = data['speeches']
                        logger.info(f"🎙️ Found 'speeches' key with {len(speeches) if isinstance(speeches, list) else 'non-list'} items")
                    elif 'results' in data:
                        speeches = data['results']
                        logger.info(f"🎙️ Found 'results' key with {len(speeches) if isinstance(speeches, list) else 'non-list'} items")
                    else:
                        # The data might be the speeches directly
                        speeches = data
                        logger.info(f"🎙️ Using data directly as speeches (type: {type(speeches)})")
                    
                    if isinstance(speeches, list):
                        logger.info(f"✅ Returning {len(speeches)} speeches")
                        if speeches and len(speeches) > 0:
                            logger.info(f"📝 First speech keys: {list(speeches[0].keys()) if isinstance(speeches[0], dict) else 'Not a dict'}")
                        return speeches
                    else:
                        logger.warning(f"⚠️ Speeches is not a list: {type(speeches)}")
                        return []
                        
                elif isinstance(data, list):
                    logger.info(f"✅ Data is a list with {len(data)} items")
                    return data
                else:
                    logger.warning(f"⚠️ Data is neither dict nor list: {type(data)}")
                    return []
            else:
                # Fallback for unexpected response format
                logger.warning(f"⚠️ Unexpected response format: {type(response)}")
                logger.warning(f"⚠️ Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
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
        
        logger.info(f"🔄 Starting paginated fetch with folder={folder}, source={source}")
        
        try:
            while True:
                page_count += 1
                logger.info(f"📄 Fetching page {page_count}...")
                
                # Get a batch of speeches with large page size
                response = self.otter.get_speeches(folder=folder, page_size=500, source=source)
                
                logger.info(f"📡 Page {page_count} response type: {type(response)}")
                if response:
                    logger.info(f"📡 Page {page_count} response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
                
                if response is None or not isinstance(response, dict) or 'data' not in response:
                    logger.warning(f"⚠️ Page {page_count} has invalid response structure, stopping")
                    break
                    
                data = response['data']
                logger.info(f"📊 Page {page_count} data type: {type(data)}")
                logger.info(f"📊 Page {page_count} data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # Extract speeches from this batch
                if isinstance(data, dict):
                    batch_speeches = data.get('speeches', [])
                    end_of_list = data.get('end_of_list', True)
                    last_load_ts = data.get('last_load_ts')
                    
                    logger.info(f"🎙️ Page {page_count}: {len(batch_speeches) if isinstance(batch_speeches, list) else 'non-list'} speeches, end_of_list={end_of_list}")
                    
                    if isinstance(batch_speeches, list):
                        all_speeches.extend(batch_speeches)
                        logger.info(f"📈 Total speeches so far: {len(all_speeches)}")
                    
                    # Check if we've reached the end
                    if end_of_list:
                        logger.info(f"🏁 Reached end of list on page {page_count}")
                        break
                        
                    # Safety check to prevent infinite loops
                    if page_count > 100:  # Max 50,000 speeches
                        logger.warning(f"⚠️  Safety limit reached: {page_count} pages, {len(all_speeches)} speeches")
                        break
                else:
                    logger.warning(f"⚠️ Page {page_count} data is not a dict: {type(data)}")
                    break
            
            logger.info(f"✅ Completed pagination: {len(all_speeches)} total speeches across {page_count} pages")
            return all_speeches
            
        except OtterAIException as e:
            logger.exception("Failed to fetch all speeches - OtterAI API error")
            raise Exception(f"Failed to fetch all speeches: {str(e)}")
        except Exception as e:
            logger.exception("Error fetching all speeches - general error")
            raise Exception(f"Error fetching all speeches: {str(e)}")
    
    def get_speeches_batch(self, batch_size: int = 50, folder: int = 0, source: str = "owned"):
        """
        Generator that yields batches of speeches for efficient processing
        
        Args:
            batch_size: Number of speeches per batch (default: 50)
            folder: Folder ID to search in
            source: Source type ("owned", "shared", etc.)
            
        Yields:
            List[Dict]: Batch of speech dictionaries
        """
        if not self.authenticated or not self.otter:
            raise Exception("Not authenticated. Please login first.")
            
        page_count = 0
        total_yielded = 0
        
        logger.info(f"🔄 Starting batch processing with batch_size={batch_size}, folder={folder}, source={source}")
        
        try:
            while True:
                page_count += 1
                logger.info(f"📄 Fetching batch {page_count} (size: {batch_size})...")
                
                # Get a batch of speeches with the specified batch size
                response = self.otter.get_speeches(folder=folder, page_size=batch_size, source=source)
                
                if response is None or not isinstance(response, dict) or 'data' not in response:
                    logger.warning(f"⚠️ Batch {page_count} has invalid response structure, stopping")
                    break
                    
                data = response['data']
                
                # Extract speeches from this batch
                if isinstance(data, dict):
                    batch_speeches = data.get('speeches', [])
                    end_of_list = data.get('end_of_list', True)
                    
                    logger.info(f"🎙️ Batch {page_count}: {len(batch_speeches)} speeches, end_of_list={end_of_list}")
                    
                    if isinstance(batch_speeches, list) and len(batch_speeches) > 0:
                        total_yielded += len(batch_speeches)
                        logger.info(f"📈 Yielding batch of {len(batch_speeches)} speeches (total so far: {total_yielded})")
                        yield batch_speeches
                    
                    # Check if we've reached the end
                    if end_of_list or len(batch_speeches) == 0:
                        logger.info(f"🏁 Reached end of list on batch {page_count}")
                        break
                        
                    # Safety check to prevent infinite loops
                    if page_count > 200:  # Max 10,000 speeches with batch_size=50
                        logger.warning(f"⚠️  Safety limit reached: {page_count} batches, {total_yielded} speeches")
                        break
                else:
                    logger.warning(f"⚠️ Batch {page_count} data is not a dict: {type(data)}")
                    break
            
            logger.info(f"✅ Completed batch processing: {total_yielded} total speeches across {page_count} batches")
                
        except OtterAIException as e:
            logger.exception("Failed to fetch speech batches - OtterAI API error")
            raise Exception(f"Failed to fetch speech batches: {str(e)}")
        except Exception as e:
            logger.exception("Error fetching speech batches - general error")
            raise Exception(f"Error fetching speech batches: {str(e)}")

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
