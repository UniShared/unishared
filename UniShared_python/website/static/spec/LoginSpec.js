describe("Login", function() {
    beforeEach(function() {
        jasmine.getFixtures().fixturesPath = '/jasmine/fixtures';
        loadFixtures("registration/login.html");
        
        login.init();
        
        $container_student_lifelonglearner = $('#container_student_lifelonglearner');
        $container_school = $('#container_school');
        $container_gmail = $('#container_gmail');
    });
    
    describe('student / lifelong learner screen', function() {
        it("should be visible at start", function() {
            expect($container_student_lifelonglearner).toBe('div');
            expect($container_student_lifelonglearner).not.toBeHidden();
        });
        
        it("should contain a student button", function () {
            expect($container_student_lifelonglearner).toContain('a.form_student');
        });
        
        it("should contain a life long learner button", function () {
            expect($container_student_lifelonglearner).toContain('a.form_lifelonglearner');
        });
        
        it("should go to school screen when student clicked", function() {
            login.goToContainerSchool();
            
            expect($container_student_lifelonglearner.is(":visible")).toBe(false);
            expect($container_school.is(":visible")).toBe(true);
            expect($container_gmail.is(":visible")).toBe(false);
        });
        
        it("should go to gmail screen when life long learner clicked", function() {
            $('.form_lifelonglearner').click();
            waits(510);
            
            runs(function () {
                expect($container_student_lifelonglearner.is(":visible")).toBe(false); 
                expect($container_gmail.is(":visible")).toBe(true);
                expect($container_school).toBeHidden();    
            });
        });
    });

    it("should contain school screen", function() {
        expect($container_school).toBe('div');
        expect($container_school).toContain('.prev_button');
        expect($container_school).toContain('.next_button');
    });

    it("should contain gmail screen", function() {
        expect($container_gmail).toBe('div');
        expect($container_gmail).toContain('.prev_button');
        expect($container_gmail).toContain('.next_button');
    });
}); 