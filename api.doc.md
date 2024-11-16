## Websocket Endpoint: `ws://{host}/tracking/{order_id}`

**Description:** Return the tracking information of the order in real-time.

**Response:**
```json
{
    "type": "location_update",
    "data": {
        "order_id": "integer",
        "latitude": "float",
        "longitude": "float"
    }
}
```

## Websocket Endpoint: `ws://{host}/customer`

**Description:** Notify the customer with new information.

**Response:**
```json
{
    "type": "notification",
    "data": {
        "order_id": "integer",
        "message": "string"
    }
}
```

## Websocket Endpoint: `ws://{host}/shipper`

**Description:** Notify the shipper with new shipping route

**Response:**
```json
{
    "type": "new_order",
    "data": {
        "locations": [
            {
                "location_id": "integer",
                "latitude": "float",
                "longitude": "float",
                "pickup_orders": [
                    {
                        "order_id": "int",
                        "size": "str",
                        "weight": "float"
                    }
                ],
                "dropoff_orders": [
                    {
                        "order_id": "integer",
                        "size": "str",
                        "weight": "float"
                    }
                ]
            }
        ]
    }
}
```