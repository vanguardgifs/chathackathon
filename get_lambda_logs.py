import boto3
import datetime
from botocore.exceptions import ClientError

def get_logs_for_function(function_name, hours=24):
    """
    Retrieve and format CloudWatch logs for a specified Lambda function.
    
    Args:
        function_name (str): Name of the Lambda function
        hours (int, optional): Number of hours of logs to retrieve. Defaults to 24.
        
    Returns:
        str: A formatted string containing all the logs
    """
    # Calculate start and end times
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(hours=hours)
    
    # Convert datetime objects to milliseconds since epoch (required by CloudWatch API)
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = int(end_time.timestamp() * 1000)
    
    # Create CloudWatch Logs client
    logs_client = boto3.client('logs')
    
    # Lambda log group name follows the pattern: /aws/lambda/{function_name}
    log_group_name = f"/aws/lambda/{function_name}"
    
    try:
        # First, get all log streams in the log group, sorted by most recent first
        log_streams_response = logs_client.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True
        )
        
        log_streams = log_streams_response.get('logStreams', [])
        
        if not log_streams:
            return f"No log streams found for Lambda function: {function_name}"
        
        all_events = []
        
        # For each log stream, get the events within our time range
        for stream in log_streams:
            stream_name = stream['logStreamName']
            
            try:
                # Get log events for this stream
                log_events_response = logs_client.get_log_events(
                    logGroupName=log_group_name,
                    logStreamName=stream_name,
                    startTime=start_time_ms,
                    endTime=end_time_ms,
                    limit=10000  # Adjust as needed
                )
                
                events = log_events_response.get('events', [])
                
                # Add stream name to each event for reference
                for event in events:
                    event['logStreamName'] = stream_name
                    # Convert timestamp from milliseconds to datetime for easier reading
                    event['timestamp_dt'] = datetime.datetime.fromtimestamp(
                        event['timestamp'] / 1000.0
                    ).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                
                all_events.extend(events)
                
                # If we've collected a lot of events, we might want to stop to avoid memory issues
                if len(all_events) >= 10000:
                    warning_msg = "Warning: Reached maximum event limit (10000). Some logs may be missing."
                    break
                    
            except ClientError as e:
                error_msg = f"Error getting logs for stream {stream_name}: {e}"
                continue
        
        # Sort all events by timestamp
        all_events.sort(key=lambda x: x['timestamp'])
        
        # Format the logs as a string
        if not all_events:
            return "No log events found in the specified time range."
        
        logs_string = f"Found {len(all_events)} log events:\n"
        logs_string += "-" * 80 + "\n"
        
        for event in all_events:
            timestamp = event['timestamp_dt']
            stream = event['logStreamName']
            message = event['message'].strip()
            
            logs_string += f"[{timestamp}] [{stream}]\n"
            logs_string += f"{message}\n"
            logs_string += "-" * 80 + "\n"
        
        return logs_string
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return f"Log group not found for Lambda function: {function_name}"
        else:
            return f"Error retrieving logs: {e}"
