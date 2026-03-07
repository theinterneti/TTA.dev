# Creating a Custom Tool

This example demonstrates how to create a custom tool for the TTA project.

## Basic Tool Example

Here's how to create a simple custom tool that provides weather information:

```python
from typing import Dict, Any, Optional

from tta.src.tools.base import Tool
from tta.src.core import get_logger

# Set up logger
logger = get_logger(__name__)


class WeatherTool(Tool):
    """
    Tool for getting weather information.
    """
    
    def __init__(self, name: str = "weather", description: str = "Get weather information"):
        """
        Initialize the weather tool.
        
        Args:
            name: Tool name
            description: Tool description
        """
        super().__init__(name, description)
    
    def execute(
        self,
        location: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute the tool.
        
        Args:
            location: Location to get weather for
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Weather data
        """
        logger.info(f"Getting weather for location: {location}")
        
        # In a real implementation, you would call a weather API
        # For this example, we'll return mock data
        
        # Mock weather data
        weather_data = {
            "location": location,
            "temperature": 72,
            "condition": "Sunny",
            "humidity": 45,
            "wind_speed": 5,
        }
        
        return {
            "success": True,
            "message": f"Weather information for {location}",
            "weather": weather_data,
        }
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """
        Get the tool parameters schema.
        
        Returns:
            Dict[str, Any]: Parameters schema
        """
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location to get weather for",
                },
            },
            "required": ["location"],
        }
```

## Registering the Tool

To make your custom tool available in the game, you need to register it with the tool registry:

```python
from tta.src.tools import get_tool_registry
from .weather_tool import WeatherTool

# Get tool registry
tool_registry = get_tool_registry()

# Register the weather tool
tool_registry.register_tool(WeatherTool())
```

## Using the Tool in Commands

Once registered, you can use the tool in your game commands:

```python
from tta.src.tools import get_tool_registry

def handle_weather(game_state, location):
    """
    Handle the weather command.
    
    Args:
        game_state: Current game state
        location: Location to get weather for
        
    Returns:
        Tuple[str, Dict[str, Any]]: Narrative response and updated game state
    """
    # Get tool registry
    tool_registry = get_tool_registry()
    
    # Get weather tool
    weather_tool = tool_registry.get_tool("weather")
    
    # Execute weather tool
    result = weather_tool.execute(location=location)
    
    # Check if weather request was successful
    if not result.get("success", False):
        return f"Unable to get weather for {location}.", game_state
    
    # Get weather data
    weather = result.get("weather", {})
    
    # Create response
    response = f"The weather in {weather.get('location')} is {weather.get('condition')} with a temperature of {weather.get('temperature')}°F."
    
    return response, game_state
```

## Advanced Tool Example

For more complex tools, you might want to integrate with external APIs or services. Here's a more advanced example:

```python
import requests
from typing import Dict, Any, Optional

from tta.src.tools.base import Tool
from tta.src.core import get_logger, get_config_value, ToolError

# Set up logger
logger = get_logger(__name__)


class OpenWeatherTool(Tool):
    """
    Tool for getting weather information from OpenWeather API.
    """
    
    def __init__(
        self,
        name: str = "openweather",
        description: str = "Get weather information from OpenWeather API",
        api_key: Optional[str] = None,
    ):
        """
        Initialize the OpenWeather tool.
        
        Args:
            name: Tool name
            description: Tool description
            api_key: OpenWeather API key (default: from config)
        """
        super().__init__(name, description)
        self.api_key = api_key or get_config_value("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    def execute(
        self,
        location: str,
        units: str = "imperial",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute the tool.
        
        Args:
            location: Location to get weather for
            units: Units to use (imperial, metric, standard)
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Weather data
        """
        logger.info(f"Getting weather for location: {location}")
        
        try:
            # Make API request
            params = {
                "q": location,
                "appid": self.api_key,
                "units": units,
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Extract relevant weather data
            weather_data = {
                "location": data.get("name"),
                "temperature": data.get("main", {}).get("temp"),
                "condition": data.get("weather", [{}])[0].get("main"),
                "description": data.get("weather", [{}])[0].get("description"),
                "humidity": data.get("main", {}).get("humidity"),
                "wind_speed": data.get("wind", {}).get("speed"),
            }
            
            return {
                "success": True,
                "message": f"Weather information for {location}",
                "weather": weather_data,
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting weather: {e}")
            raise ToolError(f"Error getting weather: {e}")
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """
        Get the tool parameters schema.
        
        Returns:
            Dict[str, Any]: Parameters schema
        """
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location to get weather for",
                },
                "units": {
                    "type": "string",
                    "description": "Units to use (imperial, metric, standard)",
                    "enum": ["imperial", "metric", "standard"],
                    "default": "imperial",
                },
            },
            "required": ["location"],
        }
```

## Testing Your Tool

Create a test file for your tool to ensure it works correctly:

```python
import pytest
from unittest.mock import patch, MagicMock

from your_module.weather_tool import WeatherTool


class TestWeatherTool:
    """
    Tests for the weather tool.
    """
    
    def test_execute(self):
        """
        Test execute method.
        """
        # Create a weather tool
        tool = WeatherTool()
        
        # Execute the tool
        result = tool.execute(location="New York")
        
        # Check the result
        assert result["success"] is True
        assert "weather" in result
        assert result["weather"]["location"] == "New York"
```

For the advanced tool with API calls, you would mock the requests:

```python
import pytest
from unittest.mock import patch, MagicMock

from your_module.openweather_tool import OpenWeatherTool


class TestOpenWeatherTool:
    """
    Tests for the OpenWeather tool.
    """
    
    @patch("your_module.openweather_tool.requests.get")
    def test_execute(self, mock_get):
        """
        Test execute method.
        """
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "New York",
            "main": {
                "temp": 72,
                "humidity": 45,
            },
            "weather": [
                {
                    "main": "Clear",
                    "description": "clear sky",
                }
            ],
            "wind": {
                "speed": 5,
            },
        }
        mock_get.return_value = mock_response
        
        # Create a weather tool
        tool = OpenWeatherTool(api_key="test_key")
        
        # Execute the tool
        result = tool.execute(location="New York")
        
        # Check the result
        assert result["success"] is True
        assert "weather" in result
        assert result["weather"]["location"] == "New York"
        assert result["weather"]["temperature"] == 72
        assert result["weather"]["condition"] == "Clear"
```
