import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
from models import MLSProvider, Listing, MLSAccountInDB

logger = logging.getLogger(__name__)

class MLSIntegration:
    """
    Core MLS Integration class following RESO Web API standard.
    This class handles communication with MLS systems via RESO Web API (OData-based).
    """
    
    def __init__(self, mls_account: MLSAccountInDB):
        self.mls_account = mls_account
        self.provider = mls_account.provider
        self.api_endpoint = mls_account.api_endpoint or self._get_default_endpoint()
        self.client = httpx.AsyncClient(timeout=30.0)
        
    def _get_default_endpoint(self) -> str:
        """Get default RESO Web API endpoint for each MLS provider"""
        endpoints = {
            MLSProvider.CRMLS: "https://api.crmls.org/RESO/OData",
            MLSProvider.BRIGHT_MLS: "https://api.brightmls.com/RESO/OData",
            MLSProvider.RETS_RABBIT: "https://api.retsrabbit.com/RESO/OData",
            MLSProvider.STELLAR_MLS: "https://api.stellarmls.com/RESO/OData",
            MLSProvider.DEMO: "https://api.demo-reso.com/RESO/OData"
        }
        return endpoints.get(self.provider, "")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with MLS using OAuth2 client credentials flow.
        This is the standard authentication method for RESO Web APIs.
        """
        try:
            # For demo mode, simulate successful authentication
            if self.provider == MLSProvider.DEMO:
                logger.info(f"Demo mode: Simulating authentication for {self.provider}")
                return True
            
            # OAuth2 token endpoint (typically /oauth/token)
            token_url = f"{self.api_endpoint.rsplit('/RESO', 1)[0]}/oauth/token"
            
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.mls_account.client_id,
                'client_secret': self.mls_account.client_secret
            }
            
            response = await self.client.post(token_url, data=auth_data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                self.token_expires_at = datetime.utcnow() + timedelta(
                    seconds=token_data.get('expires_in', 3600)
                )
                logger.info(f"Successfully authenticated with {self.provider}")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            # For demo purposes, return True to allow testing
            if self.provider == MLSProvider.DEMO:
                return True
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the MLS connection by fetching metadata.
        RESO Web APIs provide metadata endpoints for validation.
        """
        try:
            if self.provider == MLSProvider.DEMO:
                return {
                    'connected': True,
                    'provider': self.provider,
                    'message': 'Demo mode - Connection simulated',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Fetch RESO metadata to verify connection
            metadata_url = f"{self.api_endpoint}/$metadata"
            headers = self._get_auth_headers()
            
            response = await self.client.get(metadata_url, headers=headers)
            
            if response.status_code == 200:
                return {
                    'connected': True,
                    'provider': self.provider,
                    'message': 'Successfully connected to MLS',
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'connected': False,
                    'provider': self.provider,
                    'message': f'Connection failed: {response.status_code}',
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Connection test error: {str(e)}")
            return {
                'connected': False,
                'provider': self.provider,
                'message': f'Error: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def publish_listing(self, listing: Listing) -> Dict[str, Any]:
        """
        Publish a listing to MLS using RESO Web API.
        This is the core functionality - publishing to MLS which then syndicates to portals.
        """
        try:
            if self.provider == MLSProvider.DEMO:
                # Simulate successful publishing in demo mode
                mls_listing_id = f"MLS{listing.id[:8].upper()}"
                logger.info(f"Demo mode: Simulating listing publication for {listing.id}")
                
                return {
                    'success': True,
                    'mls_listing_id': mls_listing_id,
                    'mls_number': mls_listing_id,
                    'message': 'Successfully published to MLS (Demo Mode)',
                    'published_at': datetime.utcnow().isoformat(),
                    'syndication_status': {
                        'zillow': 'pending',
                        'realtor_com': 'pending',
                        'trulia': 'pending'
                    }
                }
            
            # Convert listing to RESO-compliant format
            reso_listing = self._convert_to_reso_format(listing)
            
            # POST to Property endpoint
            property_url = f"{self.api_endpoint}/Property"
            headers = self._get_auth_headers()
            headers['Content-Type'] = 'application/json'
            
            response = await self.client.post(
                property_url,
                json=reso_listing,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    'success': True,
                    'mls_listing_id': result.get('ListingId'),
                    'mls_number': result.get('ListingKey'),
                    'message': 'Successfully published to MLS',
                    'published_at': datetime.utcnow().isoformat(),
                    'syndication_status': {
                        'zillow': 'syndicating',
                        'realtor_com': 'syndicating',
                        'trulia': 'syndicating'
                    }
                }
            else:
                logger.error(f"Publish failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'message': f'Failed to publish: {response.status_code}',
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Publish error: {str(e)}")
            return {
                'success': False,
                'message': f'Error publishing listing: {str(e)}'
            }
    
    async def update_listing(self, listing_id: str, listing: Listing) -> Dict[str, Any]:
        """
        Update an existing MLS listing.
        """
        try:
            if self.provider == MLSProvider.DEMO:
                return {
                    'success': True,
                    'message': 'Successfully updated MLS listing (Demo Mode)',
                    'updated_at': datetime.utcnow().isoformat()
                }
            
            reso_listing = self._convert_to_reso_format(listing)
            property_url = f"{self.api_endpoint}/Property('{listing_id}')"
            headers = self._get_auth_headers()
            headers['Content-Type'] = 'application/json'
            
            response = await self.client.patch(
                property_url,
                json=reso_listing,
                headers=headers
            )
            
            if response.status_code in [200, 204]:
                return {
                    'success': True,
                    'message': 'Successfully updated MLS listing',
                    'updated_at': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to update: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Update error: {str(e)}")
            return {
                'success': False,
                'message': f'Error updating listing: {str(e)}'
            }
    
    async def get_syndication_status(self, mls_listing_id: str) -> Dict[str, Any]:
        """
        Get syndication status from MLS.
        Check which portals the listing has been syndicated to.
        """
        try:
            if self.provider == MLSProvider.DEMO:
                return {
                    'zillow': 'active',
                    'realtor_com': 'active',
                    'trulia': 'active',
                    'homes_com': 'active',
                    'last_updated': datetime.utcnow().isoformat()
                }
            
            # Query syndication status via RESO
            status_url = f"{self.api_endpoint}/Property('{mls_listing_id}')/SyndicationRemarks"
            headers = self._get_auth_headers()
            
            response = await self.client.get(status_url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Syndication status error: {str(e)}")
            return {}
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for RESO API requests"""
        if hasattr(self, 'access_token') and self.access_token:
            return {'Authorization': f'Bearer {self.access_token}'}
        return {}
    
    def _convert_to_reso_format(self, listing: Listing) -> Dict[str, Any]:
        """
        Convert internal listing format to RESO Web API standard format.
        RESO uses specific field names defined in the Data Dictionary.
        """
        return {
            'ListingKey': listing.id,
            'PropertyType': listing.property_type.value,
            'UnparsedAddress': listing.address,
            'City': listing.city,
            'StateOrProvince': listing.state,
            'PostalCode': listing.zip_code,
            'ListPrice': listing.price,
            'BedroomsTotal': listing.bedrooms,
            'BathroomsTotalInteger': int(listing.bathrooms),
            'LivingArea': listing.square_feet,
            'LotSizeArea': listing.lot_size,
            'YearBuilt': listing.year_built,
            'PublicRemarks': listing.description,
            'ListingStatus': 'Active',
            'StandardStatus': 'Active',
            'Media': [{'MediaURL': img} for img in listing.images]
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
