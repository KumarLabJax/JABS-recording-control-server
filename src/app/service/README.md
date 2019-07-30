# Service Package

Each script here handles some portion of the business logic for a controller.
 These scripts do the work, pass their results back to the controller, which 
 then serializes them prior to returning the response to the client.
 
 Often business logic is handled by model class methods. However, this is for
  endpoints that don't have a database model.
 