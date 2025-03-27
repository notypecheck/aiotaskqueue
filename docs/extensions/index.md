# Extensions

Extensions are a way to extend aiotaskqueue, by handling certain events like
task completion or errors, they're heavily
inspired by [StrawberryGraphQL Extensions](https://strawberry.rocks/docs/guides/custom-extensions).

Multiple interfaces can be implemented by a single class to avoid having 
to register multiple extensions for a single feature.



::: aiotaskqueue.extensions.OnTaskCompletion
    options:
        show_docstring_parameters: false


::: aiotaskqueue.extensions.OnTaskException
    options:
        show_docstring_parameters: false


::: aiotaskqueue.extensions.OnTaskSchedule
    options:
        show_docstring_parameters: false
