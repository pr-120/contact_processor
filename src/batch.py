from googleapiclient.http import BatchHttpRequest


def create_batch_request(service_name: str, result_list: list):
    """
    creates an empty batch for the corresponding service
    :param service_name: string specifying the service that is used with this batch
    :param result_list: list for result collection
    :return: BatchHttpRequest object
    """

    def callback(request_id, response, exception):
        if exception:
            print(f"An error occurred for request {request_id}: {exception}")
            result_list.append({"id": request_id, "error": exception})
        else:
            print(f"Success")
            result_list.append({"id": request_id, "response": response})

    batch = BatchHttpRequest(batch_uri="https://" + service_name + ".googleapis.com/batch", callback=callback)

    return batch
