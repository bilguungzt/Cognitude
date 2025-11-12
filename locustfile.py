from locust import HttpUser, task, between

class CognitudeUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        """
        Set up headers. This method is called for each simulated user
        when they start.
        """
        # No authentication required for public endpoints
        pass

    @task(10)
    def get_root(self):
        """
        Simulates a request to the root endpoint.
        This is the most frequent task for this test.
        """
        self.client.get("/")

    @task(1)
    def get_docs(self):
        """
        Simulates a request to the docs endpoint.
        This is an infrequent task.
        """
        self.client.get("/docs")