from org.transcrypt.stubs.browser import *

def like_post(post_id):
    """
    Like a post using AJAX.

    Parameters:
        post_id (int): ID of the post to like.
    """
    def success_callback(response):
        # Get the like button by post_id and update its text with the new like count
        like_button = document.querySelector(f"#like-button-{post_id}")
        like_button.querySelector('#likeCount').innerText = f"{response['like_count']} Likes"
        
        # Toggle the button style based on whether the post is liked or not
        if response['liked']:
            like_button.classList.add('btn-primary')
            like_button.classList.remove('btn-outline-primary')
        else:
            like_button.classList.remove('btn-primary')
            like_button.classList.add('btn-outline-primary')

    window.fetch(
        f"/like_post/{post_id}",
        {"method": "POST"}
    ).then(
        lambda response: response.json().then(success_callback)
    ).catch(
        lambda error: window.console.log("Error liking post:", error)
    )

def init_dashboard_chart(labels, data):
    """
    Initialize the production trend chart.

    Parameters:
        labels (list): Years for the x-axis.
        data (list): Production values for the y-axis.
    """
    ctx = document.getElementById("productionChart").getContext("2d")
    window.Chart.new(ctx, {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": "Crop Production (tonnes)",
                "data": data,
                "borderColor": "rgba(75, 192, 192, 1)",
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "fill": True,
                "tension": 0
            }]
        },
        "options": {
            "scales": {
                "x": {"title": {"display": True, "text": "Year"}},
                "y": {"title": {"display": True, "text": "Production (tonnes)"}}
            }
        }
    })
