/**
 * Mock Mediator for communication between reader components.
 * This object will facilitate the observer pattern, allowing components
 * to subscribe to events and publish events.
 */
const MockMediator = {
    events: {},

    /**
     * Subscribes a callback function to an event.
     * @param {string} eventName - The name of the event to subscribe to.
     * @param {function} callback - The function to call when the event is published.
     */
    subscribe: function(eventName, callback) {
        if (!this.events[eventName]) {
            this.events[eventName] = [];
        }
        this.events[eventName].push(callback);
        console.log(`MockMediator: Subscribed to ${eventName}`);
    },

    /**
     * Publishes an event, calling all subscribed callbacks with the given data.
     * @param {string} eventName - The name of the event to publish.
     * @param {object} data - The data to pass to the event callbacks.
     */
    publish: function(eventName, data) {
        if (this.events[eventName]) {
            console.log(`MockMediator: Publishing ${eventName} with data:`, data);
            this.events[eventName].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in callback for event ${eventName}:`, error);
                }
            });
        } else {
            console.log(`MockMediator: No subscribers for event ${eventName}`);
        }
    }
};

// Example of how components might use the mediator:
// To publish an event:
// MockMediator.publish('mainReaderChapterChanged', { book: 'Genesis', chapter: 1 });

// To subscribe to an event:
// MockMediator.subscribe('mainReaderChapterChanged', function(data) {
//     console.log('Second reader received chapter change:', data);
//     // Logic to update the second reader
// });

// MockMediator.subscribe('strongsNumberClicked', function(data) {
//    console.log('Main reader received strongs number click:', data);
//    // Logic to display Strong's number definition
// });
